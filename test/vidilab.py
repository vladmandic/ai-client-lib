"""Standalone VidLab smoke tests for the unified client."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli.client import Client
from cli.core import ProviderError
from srv.logger import init, log
from test.helpers import parse_kwargs, process_response

IMAGE_MODELS = {
    "nano-banana-2": {"resolution": "0.5k", "max_cost_usd": 0.25},
    "gpt-image-2": {"resolution": "1k", "max_cost_usd": 0.25},
}
VIDEO_MODELS = {
    "seedance-2.5-flash": {"resolution": "480p", "max_cost_usd": 1.0},
    "wan-3.0": {"resolution": "480p", "max_cost_usd": 1.0},
    "kling-4.0": {"resolution": "720p", "max_cost_usd": 1.0},
}
PROMPTS = {
    "t2i": "Create a crisp natural-history photograph of a red fox crossing a frost-covered alpine meadow at sunrise, wide composition and realistic fur.",
    "i2i": "Give this beach portrait a polished editorial color grade, preserve the subject's existing outfit and pose, and gently enhance the sunset reflection on the water.",
    "t2v": "A red kite circles above a rugged coastline as waves break below; track smoothly along the shore, ending on a distant lighthouse in sea mist.",
    "i2v": "Animate the beach portrait with a light breeze moving the hair and gentle ripples catching the sunset; keep the subject's appearance and outfit unchanged as the camera slowly pushes in.",
}


def _output_path(output_dir: Path, model: str, workflow: str) -> Path:
    extension = ".png" if workflow in {"t2i", "i2i"} else ".mp4"
    return output_dir / f"vidilab-{model.replace('.', '-')}-{workflow}{extension}"


def _run(
    client: Client,
    model: str,
    workflow: str,
    prompt: str,
    image: str | None,
    output: Path,
    kwargs: dict[str, Any],
    webhook: str | None = None,
) -> None:
    request = {
        "model": model,
        "prompt": prompt,
        "workflow": workflow,
        **kwargs,
    }
    if image is not None:
        request["image"] = image
    log.info('VidLab request: model="%s" workflow="%s" image="%s"', model, workflow, image)
    if webhook:
        response = client.submit_async(**request, webhook=webhook)
    else:
        response = client.submit(**request)
    process_response(client, response, output)
    if webhook:
        return
    if response.status != "completed":
        raise RuntimeError(f"VidLab generation {response.request_id} did not complete: {response.error}")
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"VidLab generation {response.request_id} produced no saved media at {output}")


def _all_cases() -> list[tuple[str, str, str | None, dict[str, Any]]]:
    cases = []
    for model, options in IMAGE_MODELS.items():
        cases.append((model, "t2i", None, {**options, "aspect_ratio": "1:1"}))
        cases.append((model, "i2i", "samples/natgeo.jpg", {**options, "aspect_ratio": "1:1"}))
    for model, options in VIDEO_MODELS.items():
        video_options = {**options, "duration": 5, "aspect_ratio": "16:9"}
        cases.append((model, "t2v", None, video_options))
        image_options = dict(video_options)
        if model == "seedance-2.5-flash":
            image_options["image_mode"] = "first_frame"
        cases.append((model, "i2v", "samples/natgeo.jpg", image_options))
    return cases


def main() -> None:
    init()
    parser = argparse.ArgumentParser(description="Test VidLab image and video generation")
    parser.add_argument("--all", action="store_true", help="Run all documented model/workflow combinations")
    parser.add_argument("--model", help="VidLab model identifier")
    parser.add_argument("--workflow", choices=("t2i", "i2i", "t2v", "i2v"), help="Generation workflow")
    parser.add_argument("--prompt", help="Generation prompt (required for a single run)")
    parser.add_argument("--image", default=None, help="Optional image URL or local path")
    parser.add_argument("--webhook", default=None, help="Optional HTTPS callback for async submission")
    parser.add_argument("--output", default=None, help="Optional output path for a single synchronous run")
    parser.add_argument("--output-dir", default="tmp", help="Directory for generated media in --all mode")
    parser.add_argument("--kwargs", default="{}", type=parse_kwargs, help="Model input options as a JSON object")
    args = parser.parse_args()

    if not os.environ.get("VIDILAB_API_KEY"):
        parser.error("VIDILAB_API_KEY environment variable not set")
    if args.all:
        single_run_options = (args.model, args.workflow, args.prompt, args.image, args.webhook, args.output)
        if any(single_run_options):
            parser.error("--all cannot be combined with single-run options")
    elif not args.model or not args.workflow or not args.prompt:
        parser.error("--model, --workflow, and --prompt are required unless --all is used")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client = Client(provider="vidilab")
    log.info("Client: %s", client)
    try:
        if args.all:
            failures = []
            for model, workflow, image, kwargs in _all_cases():
                prompt = f"{PROMPTS[workflow]} Variation {time.time_ns() % 1_000_000}."
                try:
                    _run(client, model, workflow, prompt, image, _output_path(output_dir, model, workflow), kwargs)
                except (ProviderError, RuntimeError) as error:
                    failure = f"{model} {workflow}: {error}"
                    failures.append(failure)
                    log.error("VidLab smoke test failed: %s", failure)
            if failures:
                raise RuntimeError(f"{len(failures)} VidLab smoke test(s) failed: {'; '.join(failures)}")
            return

        output = Path(args.output) if args.output else _output_path(output_dir, args.model, args.workflow)
        _run(
            client,
            args.model,
            args.workflow,
            args.prompt,
            args.image,
            output,
            args.kwargs,
            webhook=args.webhook,
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
