#!/usr/bin/env python3
"""Render the reusable magazine-style WeChat cover.

The active cover contract uses short title-card fields:
article_title, cover_title, cover_subtitle, highlight, and tags.
Legacy Swiss/Brutalism/Editorial V2 files are archived under
`.archive/legacy-cover-logic/` and are not part of runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import shutil
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "cover-magazine-v1.html"
PERSONA_DIR = BASE_DIR / "assets" / "creator-persona" / "poses" / "transparent"

VARIANTS = ("portrait-anchor", "diagonal-newsstand", "black-label")
PERSONA_MODES = ("half", "shoulder", "bust")
POSES = (
    "pose-03-arms-folded.png",
    "pose-01-seated-thinking.png",
    "pose-02-walking.png",
    "pose-04-reading-paper.png",
    "pose-05-pointing-trend.png",
    "pose-06-back-glance.png",
)

ACCOUNT_BRANDS = {
    "xiaocong": "熵增时刻",
    "yeluzi": "思想的野路子",
}

BROWSER_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)


def render_template(template: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def pick(options: tuple[str, ...], seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def safe_text(value: str | None, fallback: str = "") -> str:
    value = (value or fallback or "").strip()
    return html.escape(value, quote=True)


def fit_text(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)] + "…"


def title_size_class(title: str) -> str:
    length = len(title.strip())
    if length <= 4:
        return "title-short"
    if length <= 7:
        return "title-medium"
    return "title-long"


def resolve_persona(cli_value: str | None, seed: str) -> Path:
    if cli_value:
        path = Path(cli_value).expanduser().resolve()
    else:
        path = (PERSONA_DIR / pick(POSES, seed + ":pose")).resolve()
    if not path.exists():
        raise SystemExit(f"persona image not found: {path}")
    return path


def add_legacy_args(parser: argparse.ArgumentParser) -> None:
    # Kept only so old manual commands fail less abruptly while producing the
    # new magazine cover. These values no longer control the visual system.
    for name in (
        "--meta-left",
        "--meta-right-line1",
        "--meta-right-line2",
        "--title-line1",
        "--title-line2",
        "--kicker-text",
        "--pill-1",
        "--pill-2",
        "--pill-3",
        "--pill-4",
        "--pill-5",
        "--impact-top",
        "--impact-main",
        "--impact-sub",
    ):
        parser.add_argument(name, default="")


def find_system_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if "/" in candidate:
            path = Path(candidate)
            if path.exists():
                return str(path)
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def render_with_playwright(tmp_html: Path, out: Path) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 900, "height": 383}, device_scale_factor=2)
            page.goto(tmp_html.as_uri(), wait_until="networkidle")
            page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready : true")
            page.screenshot(path=str(out))
            browser.close()
        return True
    except Exception:
        return False


def render_with_system_browser(tmp_html: Path, out: Path) -> None:
    browser = find_system_browser()
    if not browser:
        raise RuntimeError(
            "Cover rendering requires Python Playwright or a system Chrome/Chromium browser. "
            "Install requirements.txt, run `python3 -m playwright install chromium`, "
            "or install Google Chrome/Chromium."
        )
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=900,383",
        "--force-device-scale-factor=2",
        f"--screenshot={out}",
        tmp_html.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render reusable magazine cover")
    parser.add_argument("--account-style", required=True, choices=["xiaocong", "yeluzi"])
    parser.add_argument("--article-title", default="")
    parser.add_argument("--cover-title", default="")
    parser.add_argument("--cover-subtitle", default="")
    parser.add_argument("--highlight", default="")
    parser.add_argument("--tags", default="")
    parser.add_argument("--brand", default="")
    parser.add_argument("--variant", choices=(*VARIANTS, "auto"), default="auto")
    parser.add_argument("--persona-mode", choices=(*PERSONA_MODES, "auto"), default="auto")
    parser.add_argument("--persona", help="Path to transparent persona PNG")
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep-html", action="store_true", help="保留调试用临时 HTML")
    add_legacy_args(parser)
    args = parser.parse_args()

    article_title = args.article_title or "公众号文章"
    cover_title = args.cover_title or args.title_line1 or article_title
    cover_subtitle = args.cover_subtitle or args.title_line2 or args.kicker_text or "值得看的一次变化"
    highlight = args.highlight or args.impact_main or "新变化"
    tags = args.tags or "趋势 / 观察 / 普通人"
    brand = args.brand or ACCOUNT_BRANDS[args.account_style]

    cover_title = fit_text(cover_title, 10)
    cover_subtitle = fit_text(cover_subtitle, 18)
    highlight = fit_text(highlight, 8)
    seed = f"{args.account_style}:{article_title}:{cover_title}:{cover_subtitle}"
    variant = pick(VARIANTS, seed + ":variant") if args.variant == "auto" else args.variant
    persona_mode = pick(PERSONA_MODES, seed + ":mode") if args.persona_mode == "auto" else args.persona_mode
    persona = resolve_persona(args.persona, seed)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = render_template(template, {
        "ACCOUNT_STYLE": safe_text(args.account_style),
        "VARIANT": safe_text(variant),
        "PERSONA_MODE": safe_text(persona_mode),
        "TITLE_SIZE": safe_text(title_size_class(cover_title)),
        "BRAND": safe_text(brand),
        "ARTICLE_TITLE": safe_text(fit_text(article_title, 28)),
        "COVER_TITLE": safe_text(cover_title),
        "COVER_SUBTITLE": safe_text(cover_subtitle),
        "HIGHLIGHT": safe_text(highlight),
        "TAGS": safe_text(tags),
        "PERSONA_SRC": safe_text(persona.as_uri()),
    })

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out.with_suffix(".html")
    tmp_html.write_text(rendered, encoding="utf-8")

    if not render_with_playwright(tmp_html, out):
        render_with_system_browser(tmp_html, out)

    if not args.keep_html and tmp_html.exists():
        tmp_html.unlink()

    print(out)


if __name__ == "__main__":
    main()
