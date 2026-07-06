# AGENTS.md

Workspace instructions for ZCode agents. This is a **Hermes skill** (`xiaohu-wechat-publishing`), not a standalone app. `SKILL.md` is the runtime contract for WeChat Official Account ("公众号") tasks; the Python under `scripts/` implements what `SKILL.md` invokes. Keep `SKILL.md` and the scripts in sync — the skill text is the source of truth for how the pipeline is meant to be driven. `CLAUDE.md` is the longer companion guide; read it for detail beyond what's here.

## Run everything through the unified entry point

Never invoke a script with a bare `python3 foo.py`. Always use `run.py`, which resolves the correct interpreter via `runtime.python_bin()` (probes for a Python ≥3.10 that has `markdown`, `requests`, `PIL`, `playwright` — some hosts only have these under `python3.12`).

```bash
python3 scripts/run.py doctor.py --mode format          # env check, no WeChat creds needed
python3 scripts/run.py doctor.py --mode publish         # env check, requires creds
python3 scripts/run.py format.py --input article.md --theme newspaper --no-open
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong          # push to draft box
```

`--account` accepts a comma list for dual-account publishing (`xiaocong,yeluzi`).

## Tests

Plain `unittest`, no framework. Tests add `scripts/` to `sys.path` and import modules directly, so they run without full runtime deps.

```bash
python3 -m unittest discover -s tests                              # all tests
python3 -m unittest tests.test_publish_validation                   # one module
python3 -m unittest tests.test_publish_validation.PublishValidationTests.test_rejects_account_name_as_title  # one test
```

## Dependencies

`pip install -r requirements.txt` (Markdown, requests, Pillow, playwright). Playwright also needs `playwright install chromium`.

## Directory layout

- `SKILL.md` — main skill definition (version in YAML frontmatter); the runtime contract.
- `prompts/` — writing, markdown-element, quality/risk, and comment-reply rules. **`prompts/quality-and-risk.md` is the highest-priority writing file** (anti-low-quality + risk avoidance); it overrides other writing files on conflict. (Visual-design rules were moved out of `prompts/` — see `references/baoyu-style-index.md` + the skill text.)
- `references/` — dated workflow/debug notes. Load only the one relevant to the current task — `SKILL.md` "先读什么" maps task → file. Do not load them all. **`references/baoyu-style-index.md`** is the canonical Baoyu image-style matching index (picks among `baoyu-article-illustrator` / `baoyu-comic` / `baoyu-infographic` by article type).
- `templates/` — HTML templates for covers, body, preview, gallery.
- `themes/` — formatting theme JSON (`newspaper` is default). WeChat strips `<style>`, classes, JS, so format output **inlines every style** as `style="..."`; the publishable artifact is `article.html`, not `preview.html`.
- `scripts/` — the pipeline implementation. **`format_utils.py`** holds 4 pure helpers (`count_words`, `extract_title`, `strip_frontmatter`, `hex_to_rgb`) factored out of `format.py` for unit testing — CJK handling and style injection stay in `format.py`.
- `data/` — **`high-risk-keywords.json`** is the single source of truth for the high-risk soft-scan word list (edit this file, not code/docs). Supports string or `{"word": ..., "note": ...}` entries; `publish_history.py` falls back to a built-in minimal set if the file is missing.
- `tests/` — unittests.

## Pipeline architecture (single-responsibility scripts)

- `run.py` / `runtime.py` — interpreter resolution + script dispatch. All execution funnels through here.
- `workspace.py` — single source of truth for paths. Resolves workspace root (`WECHAT_WORKSPACE_DIR` env → `config.json` → default `~/.hermes/workspaces/wechat`), job/account dirs, token cache, theme selection, manifests. Use these helpers; don't hand-build paths.
- `format.py` — Markdown → WeChat-compatible HTML using `themes/*.json`.
- `image_injector.py` — the **only** source of body-image injection. Markdown `<!-- img:filename -->` markers resolve here; an unresolved marker is a hard failure. (`inject_body_images.py` is a CLI compatibility shim that just calls `image_injector.inject()` — don't add new logic there.)
- `publish_pipe.py` — main orchestrator: format → inject → `validate_publish_ready` → publish to draft box. `--dry-run` runs everything except the final push. Cron jobs should also pass `--fail-on-low-quality-warning` so same-account recent structure/visual similarity stops unattended publishing. This is the preferred front door for publishing.
- `publish.py` — lower-level WeChat draft-box client (token, media upload, draft create).
- `wechat_pipeline.py` — managed `build` / `validate` / `publish` workflow over the structured `jobs/<job>/<account>/` layout (used by cron / batch runs).
- Cover/body renderers — `render_cover_swiss.py` (default fast cover), `render_editorial_cover.py`, `render_editorial_body_modular.py`, etc. Render `templates/*.html` to PNG via playwright.
- `publish_history.py` — appends to `publish-history.jsonl` and runs the AI-disclosure blacklist scan.
- `doctor.py` — environment preflight; `mode_requires_accounts()` gates whether WeChat creds are required (format mode = no).

## Credentials & config

- WeChat credentials are read **only** from `~/.hermes/.env`, parsed in `publish_pipe._load_accounts_from_env()`. Format: `WECHAT_APPID_<NAME>` + `WECHAT_SECRET_<NAME>` (+ optional `WECHAT_AUTHOR_<NAME>`); `<NAME>` lowercased becomes the account key. **Never write real `app_id`/`app_secret` into `config.json` or skill files.**
- `config.json` holds non-secret config (workspace dir, default theme, image AI endpoint); `config.example.json` is the template.
- Image generation uses the **Agnes API** (`AGNES_API_KEY` env, model `agnes-image-2.1-flash` per the current Baoyu index, base `https://apihub.agnes-ai.com/v1/images/generations` — note `apihub` not `api`).

## Hard rules — enforced in code, do not bypass

Validated by `validate_publish_ready` in `publish_pipe.py`; any failure must block publishing:

- **No AI-identity disclosure** anywhere in article/cover/images. `publish_pipe.py` hard-scans the Markdown against a blacklist and fails on a hit. **This scan is a non-bypassable hard gate** — the `--skip-ai-guard` flag and `HERMES_WECHAT_SKIP_AI_GUARD` env var have been removed. Non-negotiable.
- `article.html` must exist; the H1 / `--title` must be the real headline, **not the account name**.
- No leftover `<!-- img:... -->` markers, no missing image injections, cover must exist, and every local `<img>` file referenced in the HTML must exist on disk.
- Only publish validated artifacts — don't improvise covers, edit copy, or skip validation in the publish path.

## Two accounts, distinct voices

- `xiaocong` / 熵增时刻 — tech, industry, AI, company and sector dynamics. High information density, restrained, industry-chain perspective, data-driven, low-emotion, like a friend who understands the industry explaining a complex change. Common but non-fixed organization modes: industry-chain breakdown, technology-route comparison, data-impact explainer, timeline review, counterintuitive explanation, system-change analysis.
- `yeluzi` / 思想的野路子丶 — livelihood, consumption, workplace, platform rules, everyday life. More slice-of-life and scenario-driven, but not sensationalist, not partisan, not stoking division; grounded in the lived experience of ordinary people. Common but non-fixed organization modes: concrete-scene opening, rules Q&A, platform/user comparison, ordinary-person action list, bill/order/small-shop case, before/after comparison.

Each account generates **its own** images based on article content. Do not default every article to baoyu-comic + dramatic/neutral + 1024x576; choose cover archetype and body-image type from the article, and avoid repeating the same visual pattern for the same account within 7 days.

## Conventions

- Scripts and skill text are in Chinese; comments and `print` output are Chinese. Match that when editing existing files.
- Keep task scope tight: a formatting request should not enter the publish path; a cover request should not touch article copy. Default multi-task order is writing → images → format → publish. "不改文案 / 原文直接发" means do only cover, format, and publish.
- `<!-- img:xxx -->` markers are a hard commitment — if you're unsure whether to add images, **don't add the marker first**; decide after formatting.
- Default deliverable first, then explain where you stopped. On failure, give the reason before the next step.
