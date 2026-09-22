"""Common helper functions for test scripts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from srv.logger import log


def parse_kwargs(raw: str | None) -> dict[str, Any]:
    """Parse a JSON string of additional keyword arguments."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        raise argparse.ArgumentTypeError(f"Invalid JSON string for --kwargs: {err}") from err
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"--kwargs must be a JSON object (dict), got {type(parsed).__name__}")
    return parsed


def save_images(images: list[Any], output_path: str | os.PathLike[str]) -> None:
    """Save PIL images to an output path or indexed paths if multiple images."""
    if not images:
        return
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if len(images) == 1:
        images[0].save(out_path)
        log.info(f'Output: path="{out_path}"')
        return
    for idx, img in enumerate(images):
        indexed_path = out_path.parent / f"{out_path.stem}_{idx}{out_path.suffix}"
        img.save(indexed_path)
        log.info(f'Output: path="{indexed_path}" index={idx} ')


def process_response(client: Any, response: Any, output_path: str | os.PathLike[str] | None) -> None:
    log.info(f"Response: {response}")
    log.info(f"Media URL: {response.media_url}")
    if response.media_url and response.status == "completed":
        _bytes = response.bytes
        _images = response.images
        log.info(f'Media: items={len(_bytes)} bytes={[len(b) for b in _bytes]} images={_images} save={output_path is not None}')
        if output_path:
            save_images(_images, output_path)

    log.debug(f"Response JSON: {json.dumps(response.as_dict(), indent=2)}")

    stats = client.resources.stats.records()
    log.debug(f"Stats JSON: {json.dumps(stats, indent=2)}")
