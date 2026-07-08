# Legacy Cover Logic Archive

This directory keeps pre-2026-07 cover renderers and templates for human
reference only.

Do not load this directory during normal skill execution. The runtime cover
contract now lives in:

- `prompts/title-and-cover.md`
- `references/visual-generation-light.md`
- `scripts/render_editorial_cover.py`
- `templates/cover-magazine-v1.html`

The files here are intentionally outside `scripts/` and `templates/` so future
agents do not mistake them for active cover options.
