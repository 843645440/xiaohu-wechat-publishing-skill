#!/usr/bin/env python3
"""野蛮主义封面渲染（cover-brutalism-v1.html）

简洁参数版：弱模型也能稳定填空。两个账号共用同一视觉风格，
只换 BRAND / ISSUE / TAG 等元信息。
"""
import argparse, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "cover-brutalism-v1.html"


def render(template: str, mapping: dict) -> str:
    for k, v in mapping.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brand", required=True, help="顶部品牌条 e.g. 熵增时刻 · ENTROPY")
    p.add_argument("--issue", default="VOL.05 / 2026")
    p.add_argument("--title-line1", required=True, help="标题第一行 e.g. 两个 Agent，")
    p.add_argument("--title-hl", required=True, help="红黑撞色高亮短句 e.g. 谁先翻车？")
    p.add_argument("--subtitle", required=True, help="白底斜置副线索（不给结论）")
    p.add_argument("--tag-1", default="AGENT 路线")
    p.add_argument("--tag-2", default="Skill 抽象")
    p.add_argument("--tag-3", default="上下文之争")
    p.add_argument("--stamp", default="VS · 2026")
    p.add_argument("--out", required=True)
    p.add_argument("--keep-html", action="store_true")
    args = p.parse_args()

    html = render(TEMPLATE_PATH.read_text(encoding="utf-8"), {
        "BRAND": args.brand, "ISSUE": args.issue,
        "TITLE_LINE1": args.title_line1, "TITLE_HL": args.title_hl,
        "SUBTITLE": args.subtitle,
        "TAG_1": args.tag_1, "TAG_2": args.tag_2, "TAG_3": args.tag_3,
        "STAMP": args.stamp,
    })

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".html"); tmp.write_text(html, encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width":900,"height":383}, device_scale_factor=2)
        page.goto(f"file://{tmp}", wait_until="networkidle")
        try:
            ok = page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready.then(() => document.fonts.check('40px \"XinYuGongHeXieSong\"', '中文测试')) : true")
            if ok is False:
                print("WARN: XinYuGongHeXieSong not ready, may fall back", file=sys.stderr)
        except Exception as e:
            print(f"WARN: font check failed: {e}", file=sys.stderr)
        page.screenshot(path=str(out))
        browser.close()

    if not args.keep_html and tmp.exists():
        tmp.unlink()
    print(out)


if __name__ == "__main__":
    main()
