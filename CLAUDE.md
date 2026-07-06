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
- Markdown elements: `prompts/markdown-elements.md`
- Required AI-flavor reduction: `references/humanizer-runtime.md`
- Required visual stage: `references/visual-generation-light.md`
- Optional rewrite examples: `prompts/examples.md`

Deleted/legacy workflows should not be restored: full baoyu style tables, external humanizer skill copies, old structure-signature anti-low-quality system, and long cron troubleshooting notes.

## Architecture

- `publish_pipe.py` is the main front door: format, inject images, validate, publish draft.
- `publish_history.py` keeps minimal history only: account, title, summary, media_id.
- `image_injector.py` owns body-image marker resolution.
- WeChat credentials come only from `~/.hermes/.env`.

## Hard rules

- Never add AI identity disclosure or AI-assistance statements to publishable content.
- Do not reintroduce complex structure/visual fingerprint history.
- Cron jobs should keep `--fail-on-low-quality-warning`; it now means recent title/summary similarity.
- The production goal is clear, useful, batch-friendly content that avoids obvious sensitive topics and low-value AIGC signals, not handcrafted deep research every time.
