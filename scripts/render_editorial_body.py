#!/usr/bin/env python3
"""
商业编辑风正文图渲染脚本

使用 templates/editorial-body-v1.html 渲染一张完整编辑型正文信息图。
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "editorial-body-v1.html"

FIELDS = [
    "EYEBROW", "TITLE", "SUBTITLE",
    "METRIC_LABEL", "METRIC_VALUE", "METRIC_UNIT", "METRIC_NOTE",
    "TAG_1_HEAD", "TAG_1_TITLE", "TAG_1_DESC",
    "TAG_2_HEAD", "TAG_2_TITLE", "TAG_2_DESC",
    "SECTION_1_TITLE", "P1_NAME", "P1_ROLE", "P1_CAP", "P1_UNIT", "P1_COPY",
    "P2_NAME", "P2_ROLE", "P2_CAP", "P2_UNIT", "P2_COPY",
    "P3_NAME", "P3_ROLE", "P3_CAP", "P3_UNIT", "P3_COPY",
    "SECTION_2_TITLE",
    "MAP_1_KICKER", "MAP_1_MAIN", "MAP_1_SUB",
    "MAP_2_KICKER", "MAP_2_MAIN", "MAP_2_SUB",
    "MAP_3_KICKER", "MAP_3_MAIN", "MAP_3_SUB",
    "MAP_4_KICKER", "MAP_4_MAIN", "MAP_4_SUB",
    "FOOTER_NOTE",
]


def render_template(template: str, mapping: dict[str, str]) -> str:
    html = template
    for key, value in mapping.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def main():
    parser = argparse.ArgumentParser(description="Render editorial body visual")
    for field in FIELDS:
        parser.add_argument(f"--{field.lower().replace('_', '-')}", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep-html", action="store_true", help="保留调试用临时 HTML")
    args = parser.parse_args()

    mapping = {field: getattr(args, field.lower()) for field in FIELDS}
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = render_template(template, mapping)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 800, "height": 1000}, device_scale_factor=2)
        page.goto(f"file://{tmp_html}", wait_until="networkidle")
        # Ensure local Chinese font is loaded before screenshot.
        try:
            font_ok = page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready.then(() => document.fonts.check('40px \"WenQuanYi Zen Hei\"', '中文测试美国AI')) : true")
            if font_ok is False:
                raise RuntimeError('Chinese font WenQuanYi Zen Hei failed to load; aborting screenshot to avoid tofu boxes')
        except Exception as exc:
            raise RuntimeError(f'Chinese font readiness check failed: {exc}') from exc
        page.screenshot(path=str(out), full_page=True)
        browser.close()

    if not args.keep_html and tmp_html.exists():
        tmp_html.unlink()

    print(out)


if __name__ == "__main__":
    main()
