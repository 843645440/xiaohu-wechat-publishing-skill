# xiaohu-wechat-publishing-skill

Hermes skill for WeChat Official Account content production and publishing.

## Includes
- Lightweight topic planning and risk rules
- Required AI-flavor reduction runtime
- Lightweight title and cover-copy compression
- Lightweight cover/body-image generation flow
- Formatting and draft-box publishing pipeline
- Tests

## Structure
- `SKILL.md`: main skill definition
- `prompts/`: lightweight writing guardrails and optional examples
- `references/`: required runtime modules for AI-flavor reduction and visuals
- `templates/`: cover and preview templates
- `themes/`: formatting themes
- `scripts/`: implementation helpers used by the skill
- `.archive/`: inactive historical backups; not used at runtime
- `tests/`: basic tests

## Runtime Notes

- Routine cover generation passes only text fields; `render_editorial_cover.py` selects the internal cover preset.
- Agents should not read `templates/cover-preset-pool.json` during normal runs.
- No OCR, image similarity, or visual scoring checks are part of the runtime.

## Source
Exported from a local Hermes skill workspace.
