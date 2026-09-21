"""Test script for BytePlus provider using submit."""

# pylint: disable=wrong-import-position,duplicate-code,assignment-from-no-return

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli.byteplus import BytePlus
from srv.logger import init, log


def _parse_kwargs(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        raise argparse.ArgumentTypeError(f"Invalid JSON string for --kwargs: {err}") from err
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"--kwargs must be a JSON object (dict), got {type(parsed).__name__}")
    return parsed


def main() -> None:
    init()

    parser = argparse.ArgumentParser(description="Test BytePlus provider submission")
    parser.add_argument("--model", required=True, help="BytePlus model identifier")
    parser.add_argument("--prompt", required=True, help="Generation prompt")
    parser.add_argument("--image", default=None, help="Optional image URL or local path")
    parser.add_argument("--video", default=None, help="Optional video URL or local path")
    parser.add_argument("--workflow", default=None, help="Optional workflow override")
    parser.add_argument("--webhook", default=None, help="Optional webhook for async submit")
    parser.add_argument(
        "--kwargs",
        default="{}",
        type=_parse_kwargs,
        help='Optional custom kwargs as a JSON object string',
    )
    args = parser.parse_args()

    if not os.environ.get("BYTEPLUS_API_KEY"):
        log.error("BYTEPLUS_API_KEY environment variable not set")
        sys.exit(1)

    log.info(
        f'Submit: model="{args.model}" prompt="{args.prompt}" image="{args.image}" '
        f'video="{args.video}" workflow="{args.workflow}" kwargs="{args.kwargs}"'
    )
    client = BytePlus()
    log.info(f"Client: {client}")
    try:
        kwargs = {
            "model": args.model,
            "prompt": args.prompt,
            "image": args.image,
            "video": args.video,
            "workflow": args.workflow,
        }
        if args.webhook:
            response = client.submit_async(**kwargs, webhook=args.webhook, **args.kwargs)
        else:
            response = client.submit(**kwargs, **args.kwargs)
        log.info(f"Response: {response}")

        raw = response.raw_request
        raw = json.dumps(raw, indent=2) if isinstance(raw, (dict, list)) else raw
        log.debug(f"Request JSON: {raw}")
        raw = response.raw_response
        raw = json.dumps(raw, indent=2) if isinstance(raw, (dict, list)) else raw
        log.debug(f"Response JSON: {raw}")

        stats = client.resources.stats.records()
        log.debug(f"Stats: {json.dumps(stats, indent=2)}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
