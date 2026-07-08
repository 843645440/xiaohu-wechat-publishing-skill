# CLAUDE.md

This repo is a Hermes skill for WeChat Official Account publishing. `SKILL.md` is the runtime contract; Python scripts under `scripts/` implement the pipeline.

## Commands

Always use the unified entry point:

```bash
python3 scripts/run.py doctor.py --mode format
python3 scripts/run.py doctor.py --mode publish
python3 scripts/run.py format.py --input article.md --theme newspaper --no-open
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
```

Tests:

```bash
python3 -m unittest discover -s tests
```

## Current runtime shape

The skill is intentionally lightweight. Do not load all references.

- Main routing: `SKILL.md`
- Lightweight risk guardrails: `prompts/quality-and-risk.md`
- Title and cover copy: `prompts/title-and-cover.md`
- Markdown elements: `prompts/markdown-elements.md`
- Required AI-flavor reduction: external `humanizer` skill
- Required visual stage: `references/visual-generation-light.md`

Do not read `templates/cover-preset-pool.json` during normal runs; the cover renderer consumes it internally. Deleted/legacy workflows should not be restored: full baoyu style tables, xiaohu internal humanizer files, old structure-signature anti-low-quality system, old body visual renderers, and long cron troubleshooting notes. External `humanizer` is the required AI-flavor pass.

## Architecture

- `publish_pipe.py` is the main front door: format, inject images, validate, publish draft.
- `render_editorial_cover.py` generates covers from text fields; persona/layout preset selection stays inside the script.
- `publish_history.py` keeps minimal history only: account, title, summary, media_id.
- `image_injector.py` owns body-image marker resolution.
- WeChat credentials come only from `~/.hermes/.env`.

## Hard rules

- Never add AI identity disclosure or AI-assistance statements to publishable content.
- Do not reintroduce complex structure/visual fingerprint history.
- Do not add OCR, image similarity, visual scoring, or other vision-dependent checks.
- Cron jobs should keep `--fail-on-low-quality-warning`; it now means recent title/summary similarity.
- The production goal is clear, useful, batch-friendly content that avoids obvious sensitive topics and low-value AIGC signals, not handcrafted deep research every time.
