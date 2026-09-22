import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli.client import PROVIDERS, Client
from srv.logger import init, log
from test.helpers import parse_kwargs, process_response


def main() -> None:
    init()
    parser = argparse.ArgumentParser(description="Test unified client submission")
    parser.add_argument(
        "--provider",
        required=True,
        type=str.lower,
        choices=list(PROVIDERS.keys()),
        help="Provider identifier",
    )
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("--prompt", required=True, help="Generation prompt")
    parser.add_argument("--image", default=None, help="Optional image URL or local path")
    parser.add_argument("--video", default=None, help="Optional video URL or local path")
    parser.add_argument("--workflow", default=None, help="Optional workflow override")
    parser.add_argument("--webhook", default=None, help="Optional webhook for async submit")
    parser.add_argument("--output", default=None, help="Optional output path to save PIL image")
    parser.add_argument("--kwargs", default="{}", type=parse_kwargs, help='Optional custom kwargs as a JSON object string')
    args = parser.parse_args()

    env_var = f"{args.provider.upper()}_API_KEY"
    if not os.environ.get(env_var):
        log.error(f"{env_var} environment variable not set")
        sys.exit(1)
    log.info(f'Submit: provider="{args.provider}" model="{args.model}" prompt="{args.prompt}" image="{args.image}" video="{args.video}" workflow="{args.workflow}" kwargs="{args.kwargs}"')
    client = Client(provider=args.provider)
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
