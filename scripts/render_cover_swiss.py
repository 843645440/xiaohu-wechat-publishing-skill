#!/usr/bin/env python3
"""瑞士极简风封面渲染（cover-swiss-v1.html）

米白底 + 一抹红，最安全的封面通用版式。两个账号共用风格，
仅改 brand / issue / topic 三个元信息。
"""
import argparse, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "cover-swiss-v1.html"


def render(template: str, mapping: dict) -> str:
    for k, v in mapping.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brand", required=True, help="顶部品牌条 e.g. 熵增时刻 · ENTROPY")
    p.add_argument("--title-line1", required=True, help="标题前半 e.g. 两个 AGENT，")
    p.add_argument("--title-hl", required=True, help="红字 hook 短句 e.g. 谁先翻车？")
    p.add_argument("--subtitle", required=True, help="副线索（留悬念、不给结论）")
    p.add_argument("--issue", default="VOL.05 / 2026")
    p.add_argument("--topic", default="AGENT 路线之争")
    p.add_argument("--out", required=True)
    p.add_argument("--keep-html", action="store_true")
    args = p.parse_args()

    html = render(TEMPLATE_PATH.read_text(encoding="utf-8"), {
        "BRAND": args.brand,
        "TITLE_LINE1": args.title_line1,
        "TITLE_HL": args.title_hl,
        "SUBTITLE": args.subtitle,
        "ISSUE": args.issue,
        "TOPIC": args.topic,
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
