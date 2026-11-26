# VidLab Smoke Tests

The standalone runner supports individual calls or the full documented model/workflow matrix. The full run sends ten generations (two image models with `t2i` and `i2i`, and three video models with `t2v` and `i2v`), uses `samples/natgeo.jpg` for image input, caps each request with `max_cost_usd`, and saves generated files under `tmp/`.

```bash
source venv/bin/activate
export VIDILAB_API_KEY=...
python -m test.vidilab --all
```

For a single request:

```bash
python -m test.vidilab --model nano-banana-2 --workflow t2i \
  --prompt "A red fox on a snowy alpine ridge at sunrise" --output tmp/vidilab-example.png
```

The runner's prompts vary per generation. It fails explicitly if a synchronous generation does not complete or no media file is saved. An optional `--webhook URL` exercises `submit_async` for a single request; a publicly reachable HTTPS callback URL is required for callback delivery.

## Live run results

Live run: 2026-11-25. Nine of the ten model/workflow combinations completed and were saved. VidLab rejected both GPT Image 2 image-edit attempts with `content_policy`; failed generations are not billed and no output file was produced. Video generations were five seconds each. Successful generation prices totaled $2.77.

| Model | Workflow | Result | VidLab generation ID / price | Saved output |
| --- | --- | --- | --- | --- |
| `nano-banana-2` | `t2i` | Completed | `gen_oSQKyPfNDOGWO3q1v06gFJdJ` / $0.07 | [PNG](../tmp/vidilab-nano-banana-2-t2i.png) |
| `nano-banana-2` | `i2i` | Completed | `gen_sQ01dTM1zeBqKk6IPWVYL6jH` / $0.07 | [PNG](../tmp/vidilab-nano-banana-2-i2i.png) |
| `gpt-image-2` | `t2i` | Completed | `gen_1JHbL8PXqU8CqCTN3Dc5sMO8` / $0.03 | [PNG](../tmp/vidilab-gpt-image-2-t2i.png) |
| `gpt-image-2` | `i2i` | Blocked by provider content policy on two prompt attempts; not billed | `gen_vFD4iwG6wH2XqJCTxGlvDrhF`, `gen_ikP6L9nxDYZywsdumP50pSRu` | No output |
| `seedance-2.5-flash` | `t2v` | Completed | `gen_dub1R4QZttqoeX0oaMwxrLBo` / $0.425 | [MP4](../tmp/vidilab-seedance-2-5-flash-t2v.mp4) |
| `seedance-2.5-flash` | `i2v` | Completed | `gen_RWQPxg17Iqu4sUctDqsUjRDZ` / $0.425 | [MP4](../tmp/vidilab-seedance-2-5-flash-i2v.mp4) |
| `wan-3.0` | `t2v` | Completed | `gen_DFPtya7Z0dJTvlU1oEiPcvjy` / $0.20 | [MP4](../tmp/vidilab-wan-3-0-t2v.mp4) |
| `wan-3.0` | `i2v` | Completed | `gen_Aa9RJ43v5QnBCJZ39zmWIH2c` / $0.20 | [MP4](../tmp/vidilab-wan-3-0-i2v.mp4) |
| `kling-4.0` | `t2v` | Completed | `gen_1LYd3MCGoDNmCBOuZMjPyu2Z` / $0.675 | [MP4](../tmp/vidilab-kling-4-0-t2v.mp4) |
| `kling-4.0` | `i2v` | Completed | `gen_IcsvFZfe6ci4waqcDFixa70W` / $0.675 | [MP4](../tmp/vidilab-kling-4-0-i2v.mp4) |

Async submission and status behavior are covered by mocked adapter tests. No live webhook callback was sent because the test run did not have a public callback URL.
