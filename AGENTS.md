# AGENTS.md

Workspace instructions for ZCode agents. This repo is a Hermes skill, not a standalone app. `SKILL.md` is the runtime contract; scripts under `scripts/` implement the pipeline.

## Run scripts

Never invoke repo scripts with bare `python3 foo.py`. Use `run.py`:

```bash
python3 scripts/run.py doctor.py --mode format
python3 scripts/run.py doctor.py --mode publish
python3 scripts/run.py format.py --input article.md --theme newspaper --no-open
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
```

`--account` accepts a comma list, e.g. `xiaocong,yeluzi`.

## Tests

```bash
python3 -m unittest discover -s tests
python3 -m unittest tests.test_publish_validation
```

Tests import modules from `scripts/` directly and do not need full publish credentials.

## Runtime reading policy

Keep the skill lightweight. Do not load all references.

- Main entry: `SKILL.md`
- Writing guardrails: `prompts/quality-and-risk.md`
- Markdown elements: `prompts/markdown-elements.md`
- Required AI-flavor pass: `references/humanizer-runtime.md`
- Required visual pass: `references/visual-generation-light.md`
- Optional examples: `prompts/examples.md`

Do not use deleted legacy workflows, external humanizer/visual skills, or old design docs.

## Pipeline architecture

- `run.py` / `runtime.py` — interpreter resolution and script dispatch.
- `workspace.py` — workspace paths and token cache paths.
- `format.py` — Markdown to WeChat-compatible inline-styled HTML.
- `image_injector.py` — only source of body-image injection.
- `publish_pipe.py` — format → inject → validate → publish draft.
- `publish_history.py` — AI disclosure hard scan, high-risk soft scan, minimal title/summary history.
- `doctor.py` — environment preflight.

## Hard rules

- No AI-identity disclosure in article, cover, or images. The publish path blocks this.
- Only validated artifacts may be published.
- Cron jobs should pass `--fail-on-low-quality-warning`; it now stops only on recent title/summary similarity.
- History is intentionally minimal: account, title, summary, media_id. Do not reintroduce structure or visual signatures.

## Two accounts

- `xiaocong` / 熵增时刻 — tech, industry, AI tools, company and workflow changes.
- `yeluzi` / 思想的野路子丶 — livelihood, consumption, workplace, platform rules, ordinary life.

Use natural article organization. The current goal is safe, clear, useful, batch-friendly articles with a required AI-flavor reduction pass.
