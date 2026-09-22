import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli.byteplus import BytePlus
from srv.logger import init, log
from test.helpers import parse_kwargs, process_response


def main() -> None:
    init()
    parser = argparse.ArgumentParser(description="Test BytePlus provider submission")
    parser.add_argument("--model", required=True, help="BytePlus model identifier")
    parser.add_argument("--prompt", required=True, help="Generation prompt")
    parser.add_argument("--image", default=None, help="Optional image URL or local path")
    parser.add_argument("--video", default=None, help="Optional video URL or local path")
    parser.add_argument("--workflow", default=None, help="Optional workflow override")
    parser.add_argument("--webhook", default=None, help="Optional webhook for async submit")
    parser.add_argument("--output", default=None, help="Optional output path to save PIL image")
    parser.add_argument("--kwargs", default="{}", type=parse_kwargs, help='Optional custom kwargs as a JSON object string')
    args = parser.parse_args()

    if not os.environ.get("BYTEPLUS_API_KEY"):
        log.error("BYTEPLUS_API_KEY environment variable not set")
        sys.exit(1)
    log.info(f'Submit: model="{args.model}" prompt="{args.prompt}" image="{args.image}" video="{args.video}" workflow="{args.workflow}" kwargs="{args.kwargs}"')
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
        process_response(client, response, args.output)
    finally:
        client.close()


if __name__ == "__main__":
    main()
