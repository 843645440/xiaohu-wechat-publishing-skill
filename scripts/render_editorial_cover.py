#!/usr/bin/env python3
"""Render the reusable magazine-style WeChat cover.

The active cover contract uses short title-card fields:
article_title, cover_title, cover_subtitle, and highlight.
Legacy Swiss/Brutalism/Editorial V2 files are archived under
`.archive/legacy-cover-logic/` and are not part of runtime.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "cover-magazine-v1.html"
PRESET_PATH = BASE_DIR / "templates" / "cover-preset-pool.json"
PERSONA_DIR = BASE_DIR / "assets" / "creator-persona" / "poses" / "transparent"

VARIANTS = ("portrait-anchor", "diagonal-newsstand", "black-label")
PERSONA_MODES = ("half", "shoulder", "bust")

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


def weighted_pick(options: list[dict[str, object]], seed: str) -> dict[str, object]:
    total = sum(int(item.get("weight", 1)) for item in options)
    if total <= 0:
        raise SystemExit("cover preset weights must be positive")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    cursor = int(digest[:10], 16) % total
    for item in options:
        cursor -= int(item.get("weight", 1))
        if cursor < 0:
            return item
    return options[-1]


def safe_text(value: str | None, fallback: str = "") -> str:
    value = (value or fallback or "").strip()
    return html.escape(value, quote=True)


def fit_text(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)] + "…"


def visual_width(value: str) -> float:
    width = 0.0
    for char in value.strip():
        if char.isspace():
            width += 0.32
        elif char.isascii():
            width += 0.56
        else:
            width += 1.0
    return width


def fit_visual_text(value: str, max_width: float) -> str:
    value = (value or "").strip()
    if visual_width(value) <= max_width:
        return value

    ellipsis = "…"
    budget = max_width - visual_width(ellipsis)
    output = []
    used = 0.0
    for char in value:
        char_width = visual_width(char)
        if used + char_width > budget:
            break
        output.append(char)
        used += char_width
    return "".join(output).rstrip() + ellipsis


def title_size_class(title: str) -> str:
    stripped = title.strip()
    width = visual_width(title)
    wide_chars = sum(1 for char in stripped if not char.isascii())
    ascii_chars = sum(1 for char in stripped if char.isascii() and not char.isspace())
    if width <= 4.5 and (wide_chars <= 3 or ascii_chars >= 3):
        return "title-short"
    if width <= 7.0:
        return "title-medium"
    return "title-long"


def subtitle_size_class(subtitle: str) -> str:
    width = visual_width(subtitle)
    if width <= 10.0:
        return "subtitle-short"
    if width <= 12.0:
        return "subtitle-medium"
    return "subtitle-long"


def highlight_size_class(highlight: str) -> str:
    width = visual_width(highlight)
    if width <= 5.5:
        return "highlight-short"
    if width <= 6.8:
        return "highlight-medium"
    return "highlight-long"


def issue_no(seed: str) -> str:
    digest = hashlib.sha256((seed + ":issue").encode("utf-8")).hexdigest()
    return str(100 + (int(digest[:6], 16) % 800))


def load_presets() -> list[dict[str, object]]:
    data = json.loads(PRESET_PATH.read_text(encoding="utf-8"))
    presets: list[dict[str, object]] = []
    for item in data.get("presets", []):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        try:
            weight = int(item.get("weight", 1))
        except Exception:
            weight = 1
        presets.append({
            "name": name,
            "variant": str(item.get("variant", "")).strip(),
            "persona_mode": str(item.get("persona_mode", "")).strip(),
            "persona": str(item.get("persona", "")).strip(),
            "weight": max(1, weight),
        })
    if not presets:
        raise SystemExit(f"no cover presets found: {PRESET_PATH}")
    seen: set[str] = set()
    for preset in presets:
        name = str(preset["name"])
        if name in seen:
            raise SystemExit(f"duplicate cover preset: {name}")
        seen.add(name)
        if preset["variant"] not in VARIANTS:
            raise SystemExit(f"invalid cover preset variant: {name}")
        if preset["persona_mode"] not in PERSONA_MODES:
            raise SystemExit(f"invalid cover preset persona_mode: {name}")
        if not (PERSONA_DIR / str(preset["persona"])).exists():
            raise SystemExit(f"cover preset persona image not found: {name}")
    return presets


def select_preset(
    presets: list[dict[str, object]],
    requested: str,
    account_style: str,
    seed_period: str,
    seed: str,
) -> tuple[str, dict[str, object]]:
    presets_by_name = {str(item["name"]): item for item in presets}
    if requested == "auto":
        preset = weighted_pick(presets, f"{account_style}:{seed_period}:{seed}:preset")
        return str(preset["name"]), preset
    if requested not in presets_by_name:
        raise SystemExit(f"unknown cover preset: {requested}")
    return requested, presets_by_name[requested]


def resolve_persona(cli_value: str | None, preset: dict[str, object]) -> Path:
    if cli_value:
        path = Path(cli_value).expanduser().resolve()
    else:
        path = (PERSONA_DIR / str(preset["persona"])).resolve()
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
    parser.add_argument("--preset", default="auto", help="Cover preset name, or auto")
    parser.add_argument("--seed-period", default="", help="Stable preset rotation period, e.g. 2026-07")
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
    # Kept for old commands; the active template hides category tags.
    tags = args.tags or ""
    brand = args.brand or ACCOUNT_BRANDS[args.account_style]

    cover_title = fit_visual_text(cover_title, 9.0)
    cover_subtitle = fit_visual_text(cover_subtitle, 15.0)
    highlight = fit_visual_text(highlight, 8.0)
    seed = f"{args.account_style}:{article_title}:{cover_title}:{cover_subtitle}"
    presets = load_presets()
    seed_period = args.seed_period.strip() or dt.date.today().strftime("%Y-%m")
    preset_name, preset = select_preset(presets, args.preset, args.account_style, seed_period, seed)
    variant = str(preset["variant"]) if args.variant == "auto" else args.variant
    persona_mode = str(preset["persona_mode"]) if args.persona_mode == "auto" else args.persona_mode
    persona = resolve_persona(args.persona, preset)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = render_template(template, {
        "ACCOUNT_STYLE": safe_text(args.account_style),
        "VARIANT": safe_text(variant),
        "PRESET": safe_text(preset_name),
        "PERSONA_MODE": safe_text(persona_mode),
        "TITLE_SIZE": safe_text(title_size_class(cover_title)),
        "SUBTITLE_SIZE": safe_text(subtitle_size_class(cover_subtitle)),
        "HIGHLIGHT_SIZE": safe_text(highlight_size_class(highlight)),
        "BRAND": safe_text(brand),
        "ISSUE_NO": safe_text(issue_no(seed)),
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
