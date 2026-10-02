## Integrate LumaLabs Provider
add new provider: `luma`
reference api docs:
- [t2i](https://docs.agents.lumalabs.ai/guides/images/generation/)
- [i2i](https://docs.agents.lumalabs.ai/guides/images/editing/)
- [t2v and i2v](https://docs.agents.lumalabs.ai/guides/videos/generation/)
create: `cli/luma.py`, `docs/luma.md`, `test/luma.py`
update: `cli/client.py`, `test/client.md`, `test/client.py` and any other relevant files
env variable for api key is `LUMA_API_KEY`

i've updated api key in env
test and save results to `tmp`:
- `t2i`
- `i2i` using `samples/natgeo.jpg` as input image
- `t2v` create 5sec video using a dynamic prompt
