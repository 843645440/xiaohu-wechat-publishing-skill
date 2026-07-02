# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

This repo is a **Hermes skill** (`xiaohu-wechat-publishing`), not a standalone app. `SKILL.md` is the skill's runtime contract: it routes WeChat Official Account ("公众号") tasks across writing → cover/body images → formatting → draft-box publishing. The Python under `scripts/` is the implementation those instructions invoke. When changing behavior, keep `SKILL.md` and the scripts in sync — the skill text is the source of truth for *how* the pipeline is meant to be driven.

## Commands

Always run scripts through the unified entry point — never invoke a script with a bare `python3 foo.py`. `run.py` resolves the correct interpreter via `runtime.python_bin()`, which probes for a Python ≥3.10 that has `markdown`, `requests`, `PIL`, and `playwright` (some hosts have these only under `python3.12`, not `python3`):

```bash
python3 scripts/run.py doctor.py --mode format          # env check, no WeChat creds needed
python3 scripts/run.py doctor.py --mode publish         # env check, requires creds
python3 scripts/run.py format.py --input article.md --theme newspaper --no-open
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
```

`--account` accepts a comma list for dual-account publishing (`xiaocong,yeluzi`).

### Tests

Plain `unittest`, no framework:

```bash
python3 -m unittest discover -s tests          # all tests
python3 -m unittest tests.test_publish_validation   # one module
python3 -m unittest tests.test_publish_validation.PublishValidationTests.test_rejects_account_name_as_title  # one test
```

Tests add `scripts/` to `sys.path` and import modules directly (e.g. `from publish_pipe import validate_publish_ready`), so unit tests can run without the full runtime deps.

### Dependencies

`pip install -r requirements.txt` (Markdown, requests, Pillow, playwright). Playwright also needs its browser: `playwright install chromium`.

## Architecture

The pipeline is a chain of single-responsibility scripts, with `publish_pipe.py` as the orchestrator that fuses formatting → image injection → hard validation → publish into one command.

- **`run.py` / `runtime.py`** — interpreter resolution + script dispatch. All execution funnels through here.
- **`workspace.py`** — single source of truth for paths. Resolves the workspace root (`WECHAT_WORKSPACE_DIR` env → `config.json` → default `~/.hermes/workspaces/wechat`), job/account dirs, token cache, theme selection file, manifests. Use these helpers rather than hand-building paths.
- **`format.py`** — Markdown → WeChat-compatible HTML. WeChat strips `<style>`, CSS classes, and JS, so **every style must be inlined** as `style="..."` per element. Themes come from `themes/*.json`. The publishable artifact is `article.html`, **not** `preview.html`.
- **`image_injector.py`** — the *only* source of body-image injection. Markdown `<!-- img:filename -->` markers are resolved here; an unresolved marker is a hard failure.
- **`publish_pipe.py`** — main entry. Loads per-account credentials, formats, injects, runs `validate_publish_ready`, then publishes to the draft box. `--dry-run` runs everything except the final push.
- **`publish.py`** — lower-level WeChat draft-box client (token, media upload, draft create). `publish_pipe.py` is the preferred front door.
- **`wechat_pipeline.py`** — managed `build` / `validate` / `publish` workflow over the structured `jobs/<job>/<account>/` workspace layout (used by cron / batch runs).
- **Cover/body renderers** — `render_cover_swiss.py` (default fast cover), `render_editorial_cover.py`, `render_editorial_body_modular.py`, etc. Render HTML templates (`templates/*.html`) to PNG via playwright.
- **`publish_history.py`** — appends to `publish-history.jsonl` and runs the AI-disclosure blacklist scan.
- **`doctor.py`** — environment preflight; `mode_requires_accounts()` gates whether WeChat creds are required (format mode = no).

### Credentials & config

- WeChat credentials are **only** read from `~/.hermes/.env`, parsed in `publish_pipe._load_accounts_from_env()`. Format: `WECHAT_APPID_<NAME>` + `WECHAT_SECRET_<NAME>` (+ optional `WECHAT_AUTHOR_<NAME>`); `<NAME>` lowercased becomes the account key. Never write real `app_id`/`app_secret` into `config.json` or skill files.
- `config.json` holds non-secret config (workspace dir, default theme, image AI endpoint). `config.example.json` is the template.
- Image generation uses the **Agnes API** (`AGNES_API_KEY` env, model `agnes-image-2.1-flash`, base `https://apihub.agnes-ai.com/v1/images/generations`).

## Hard rules (enforced in code — do not bypass)

These are validated by `validate_publish_ready` in `publish_pipe.py`; any failure must block publishing:

- **No AI-identity disclosure** anywhere in article/cover/images. `publish_pipe.py` hard-scans the Markdown against a blacklist and fails on a hit. **Non-bypassable** — `--skip-ai-guard` flag and `HERMES_WECHAT_SKIP_AI_GUARD` env var removed. This is non-negotiable. High-risk keyword soft-scan (warning-only) reads its word list from `data/high-risk-keywords.json`.
- `article.html` must exist; the H1 / `--title` must be the real headline, **not** the account name.
- No leftover `<!-- img:... -->` markers, no missing image injections, cover must exist, and every local `<img>` file referenced in the HTML must exist on disk.
- Only publish validated artifacts — don't improvise covers, edit copy, or skip validation in the publish path.

## Conventions

- Scripts and the skill are written in Chinese; comments and `print` output are Chinese. Match that when editing existing files.
- Keep task scope tight: a formatting request should not enter the publish path; a cover request should not touch article copy (see `SKILL.md` "任务路由").
- Two accounts have distinct editorial voices: `xiaocong` (熵增时刻 — industry/structure/density) and `yeluzi` (思想的野路子丶 — capital/conflict/emotion). They share one image set, generated in `xiaocong`'s tone.
- `references/*.md` are dated workflow/debug notes — load only the one relevant to the current task (the SKILL.md "先读什么" section maps task → file). `references/legacy-skill-full-2026-05.md` is the full historical ruleset.
