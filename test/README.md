# Test Notes

This directory contains standalone smoke test scripts and session logs for each provider adapter and the unified client.

## Test Scripts

- `test.client`: Unified `Client` CLI test runner
- `test.fal`: Direct `Fal` provider CLI test runner
- `test.kie`: Direct `Kie` provider CLI test runner
- `test.byteplus`: Direct `BytePlus` provider CLI test runner
- `test.pixverse`: Direct `Pixverse` provider CLI test runner

## Running Tests

Ensure your virtual environment is activated and the corresponding provider API key is set in your environment (e.g. `FAL_API_KEY`, `KIE_API_KEY`, `BYTEPLUS_API_KEY`, `PIXVERSE_API_KEY`).

Example:

```bash
python -m test.client --provider kie --model z-image --output samples/output-kie.png --prompt "stylish photo of a mountain"
```

## Provider Session Logs

Per-provider session logs and example outputs are recorded in:

- [client.md](client.md)
- [kie.md](kie.md)
- [fal.md](fal.md)
- [byteplus.md](byteplus.md)
- [pixverse.md](pixverse.md)
