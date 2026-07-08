#!/usr/bin/env python3
"""
商业编辑风封面渲染脚本

默认使用 templates/editorial-cover-v2.html
支持熵增 / 野路子双账号同系统差异化渲染。
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "editorial-cover-v2.html"


def render_template(template: str, mapping: dict[str, str]) -> str:
    html = template
    for key, value in mapping.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def main():
    parser = argparse.ArgumentParser(description="Render editorial cover")
    parser.add_argument("--account-style", required=True, choices=["xiaocong", "yeluzi"])
    parser.add_argument("--meta-left", required=True)
    parser.add_argument("--meta-right-line1", required=True)
    parser.add_argument("--meta-right-line2", required=True)
    parser.add_argument("--title-line1", required=True)
    parser.add_argument("--title-line2", required=True)
    parser.add_argument("--kicker-text", required=True)
    parser.add_argument("--pill-1", required=True)
    parser.add_argument("--pill-2", required=True)
    parser.add_argument("--pill-3", required=True)
    parser.add_argument("--pill-4", required=True)
    parser.add_argument("--pill-5", required=True)
    parser.add_argument("--impact-top", required=True)
    parser.add_argument("--impact-main", required=True)
    parser.add_argument("--impact-sub", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep-html", action="store_true", help="保留调试用临时 HTML")
    args = parser.parse_args()

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = render_template(template, {
        "ACCOUNT_STYLE": args.account_style,
        "META_LEFT": args.meta_left,
        "META_RIGHT_LINE1": args.meta_right_line1,
        "META_RIGHT_LINE2": args.meta_right_line2,
        "TITLE_LINE1": args.title_line1,
        "TITLE_LINE2": args.title_line2,
        "KICKER_TEXT": args.kicker_text,
        "PILL_1": args.pill_1,
        "PILL_2": args.pill_2,
        "PILL_3": args.pill_3,
        "PILL_4": args.pill_4,
        "PILL_5": args.pill_5,
        "IMPACT_TOP": args.impact_top,
        "IMPACT_MAIN": args.impact_main,
        "IMPACT_SUB": args.impact_sub,
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 900, "height": 383}, device_scale_factor=2)
        page.goto(f"file://{tmp_html}", wait_until="networkidle")
        # Ensure local Chinese font is loaded before screenshot; otherwise Chromium may
        # silently fall back to tofu boxes in headless Linux environments.
        try:
            font_ok = page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready.then(() => document.fonts.check('40px \"XinYuGongHeXieSong\"', '中文测试美国AI') || document.fonts.check('40px \"WenQuanYi Zen Hei\"', '中文测试美国AI')) : true")
            if font_ok is False:
                raise RuntimeError('Chinese font (XinYuGongHeXieSong/WenQuanYi Zen Hei) failed to load; aborting screenshot to avoid tofu boxes')
        except Exception as exc:
            raise RuntimeError(f'Chinese font readiness check failed: {exc}') from exc
        page.screenshot(path=str(out))
        browser.close()

    if not args.keep_html and tmp_html.exists():
        tmp_html.unlink()

    print(out)


if __name__ == "__main__":
    main()
