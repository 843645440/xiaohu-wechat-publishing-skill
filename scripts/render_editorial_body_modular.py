#!/usr/bin/env python3
"""
商业编辑风正文单图渲染脚本（模块化）

输出固定单张模块图，而不是整页长图。
支持三种正式模式：hero / people / structure
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "editorial-body-modular-v1.html"


def render_template(template: str, mapping: dict[str, str]) -> str:
    html = template
    for key, value in mapping.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def hero_block(args) -> str:
    return f"""
    <div class=\"metric-panel\">
      <div>
        <div class=\"metric-label\">{args.metric_label}</div>
        <div><span class=\"metric-value\">{args.metric_value}</span><span class=\"metric-unit\">{args.metric_unit}</span></div>
        <div class=\"metric-note\">{args.metric_note}</div>
      </div>
      <div class=\"side-stack\">
        <div class=\"card\">
          <div class=\"mini-head\">{args.tag_1_head}</div>
          <div class=\"card-title\">{args.tag_1_title}</div>
          <div class=\"card-desc\">{args.tag_1_desc}</div>
        </div>
        <div class=\"card\">
          <div class=\"mini-head red\">{args.tag_2_head}</div>
          <div class=\"card-title\">{args.tag_2_title}</div>
          <div class=\"card-desc\">{args.tag_2_desc}</div>
        </div>
      </div>
    </div>
    <div class=\"quote-box\"><div class=\"quote-text\">{args.quote_text}</div></div>
    """


def people_block(args) -> str:
    return f"""
    <div class=\"section-title\">{args.section_title}</div>
    <div class=\"people-grid\" style=\"grid-template-columns: 1fr; gap:10px; margin-top:16px;\">
      <div class=\"card\" style=\"min-height:0; padding:16px 18px 14px; border-radius:22px; display:grid; grid-template-columns: .9fr 1.1fr auto; gap:14px; align-items:start;\">
        <div>
          <div class=\"mini-head\">AI / 芯片</div>
          <div class=\"person-name\" style=\"font-size:30px;\">{args.p1_name}</div>
          <div class=\"person-role\" style=\"font-size:17px; line-height:1.38;\">{args.p1_role}</div>
        </div>
        <div>
          <div class=\"person-copy\" style=\"font-size:18px; line-height:1.48; margin-top:2px;\">{args.p1_copy}</div>
        </div>
        <div style=\"text-align:right; min-width:132px;\">
          <div style=\"font-size:58px; font-weight:950; letter-spacing:-3px; color:rgba(24,49,83,.08); line-height:1;\">01</div>
          <div class=\"person-cap\" style=\"margin-top:18px; padding-top:12px; justify-content:flex-end;\"><span class=\"cap-value\" style=\"font-size:40px;\">{args.p1_cap}</span><span class=\"cap-unit\" style=\"font-size:18px;\">{args.p1_unit}</span></div>
        </div>
      </div>
      <div class=\"card\" style=\"min-height:0; padding:16px 18px 14px; border-radius:22px; display:grid; grid-template-columns: .9fr 1.1fr auto; gap:14px; align-items:start;\">
        <div>
          <div class=\"mini-head\" style=\"background:#8f1711;\">消费 / 制造</div>
          <div class=\"person-name\" style=\"font-size:30px;\">{args.p2_name}</div>
          <div class=\"person-role\" style=\"font-size:17px; line-height:1.38;\">{args.p2_role}</div>
        </div>
        <div>
          <div class=\"person-copy\" style=\"font-size:18px; line-height:1.48; margin-top:2px;\">{args.p2_copy}</div>
        </div>
        <div style=\"text-align:right; min-width:132px;\">
          <div style=\"font-size:58px; font-weight:950; letter-spacing:-3px; color:rgba(24,49,83,.08); line-height:1;\">02</div>
          <div class=\"person-cap\" style=\"margin-top:18px; padding-top:12px; justify-content:flex-end;\"><span class=\"cap-value\" style=\"font-size:40px;\">{args.p2_cap}</span><span class=\"cap-unit\" style=\"font-size:18px;\">{args.p2_unit}</span></div>
        </div>
      </div>
      <div class=\"card\" style=\"min-height:0; padding:16px 18px 14px; border-radius:22px; display:grid; grid-template-columns: .9fr 1.1fr auto; gap:14px; align-items:start;\">
        <div>
          <div class=\"mini-head\" style=\"background:#b98a18; color:#1a1a1a;\">资本 / 预期</div>
          <div class=\"person-name\" style=\"font-size:30px;\">{args.p3_name}</div>
          <div class=\"person-role\" style=\"font-size:17px; line-height:1.38;\">{args.p3_role}</div>
        </div>
        <div>
          <div class=\"person-copy\" style=\"font-size:18px; line-height:1.48; margin-top:2px;\">{args.p3_copy}</div>
        </div>
        <div style=\"text-align:right; min-width:132px;\">
          <div style=\"font-size:58px; font-weight:950; letter-spacing:-3px; color:rgba(24,49,83,.08); line-height:1;\">03</div>
          <div class=\"person-cap\" style=\"margin-top:18px; padding-top:12px; justify-content:flex-end;\"><span class=\"cap-value\" style=\"font-size:40px;\">{args.p3_cap}</span><span class=\"cap-unit\" style=\"font-size:18px;\">{args.p3_unit}</span></div>
        </div>
      </div>
    </div>
    """


def structure_block(args) -> str:
    return f"""
    <div class=\"structure-grid\" style=\"grid-template-columns: 1fr; gap:7px; margin-top:12px;\">
      <div class=\"card\" style=\"padding:12px 14px 10px; border-radius:18px;\">
        <div class=\"metric-label\" style=\"font-size:16px;\">结构判断</div>
        <div class=\"card-title\" style=\"margin-top:5px; font-size:28px; line-height:1.16;\">访华团不是企业名单，而是四类力量同时入场</div>
        <div class=\"card-desc\" style=\"margin-top:6px; font-size:16px; line-height:1.36;\">不是看谁来了，而是看四类力量为何会同时出现在一张桌子上。</div>
      </div>
      <div class=\"card\" style=\"padding:11px 14px 9px; border-radius:18px; border-left:6px solid #183153;\">
        <div class=\"mini-head\" style=\"padding:4px 8px; font-size:13px;\">{args.m1_kicker}</div>
        <div class=\"card-title\" style=\"margin-top:6px; font-size:24px;\">{args.m1_main}</div>
        <div class=\"card-desc\" style=\"margin-top:5px; font-size:15px; line-height:1.34;\">{args.m1_sub}</div>
      </div>
      <div class=\"card\" style=\"padding:11px 14px 9px; border-radius:18px; border-left:6px solid #b42318;\">
        <div class=\"mini-head red\" style=\"padding:4px 8px; font-size:13px;\">{args.m2_kicker}</div>
        <div class=\"card-title\" style=\"margin-top:6px; font-size:24px;\">{args.m2_main}</div>
        <div class=\"card-desc\" style=\"margin-top:5px; font-size:15px; line-height:1.34;\">{args.m2_sub}</div>
      </div>
      <div class=\"card\" style=\"padding:11px 14px 9px; border-radius:18px; border-left:6px solid #b98a18;\">
        <div class=\"mini-head\" style=\"background:#b98a18; color:#1a1a1a; padding:4px 8px; font-size:13px;\">{args.m3_kicker}</div>
        <div class=\"card-title\" style=\"margin-top:6px; font-size:24px;\">{args.m3_main}</div>
        <div class=\"card-desc\" style=\"margin-top:5px; font-size:15px; line-height:1.34;\">{args.m3_sub}</div>
      </div>
      <div class=\"card\" style=\"padding:11px 14px 9px; border-radius:18px; border-left:6px solid #222;\">
        <div class=\"mini-head\" style=\"background:#222; color:#fff; padding:4px 8px; font-size:13px;\">{args.m4_kicker}</div>
        <div class=\"card-title\" style=\"margin-top:6px; font-size:24px;\">{args.m4_main}</div>
        <div class=\"card-desc\" style=\"margin-top:5px; font-size:15px; line-height:1.34;\">{args.m4_sub}</div>
      </div>
    </div>
    <div class=\"quote-box\" style=\"margin-top:8px; padding:12px 14px 10px;\"><div class=\"quote-text\" style=\"font-size:17px; line-height:1.42;\">{args.quote_text}</div></div>
    """


def main():
    parser = argparse.ArgumentParser(description="Render modular editorial body card")
    parser.add_argument("--mode", required=True, choices=["hero", "people", "structure"])
    parser.add_argument("--eyebrow", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--footer-note", required=True)
    parser.add_argument("--quote-text", default="")

    parser.add_argument("--metric-label", default="")
    parser.add_argument("--metric-value", default="")
    parser.add_argument("--metric-unit", default="")
    parser.add_argument("--metric-note", default="")
    parser.add_argument("--tag-1-head", default="")
    parser.add_argument("--tag-1-title", default="")
    parser.add_argument("--tag-1-desc", default="")
    parser.add_argument("--tag-2-head", default="")
    parser.add_argument("--tag-2-title", default="")
    parser.add_argument("--tag-2-desc", default="")

    parser.add_argument("--section-title", default="")
    parser.add_argument("--p1-name", default="")
    parser.add_argument("--p1-role", default="")
    parser.add_argument("--p1-cap", default="")
    parser.add_argument("--p1-unit", default="")
    parser.add_argument("--p1-copy", default="")
    parser.add_argument("--p2-name", default="")
    parser.add_argument("--p2-role", default="")
    parser.add_argument("--p2-cap", default="")
    parser.add_argument("--p2-unit", default="")
    parser.add_argument("--p2-copy", default="")
    parser.add_argument("--p3-name", default="")
    parser.add_argument("--p3-role", default="")
    parser.add_argument("--p3-cap", default="")
    parser.add_argument("--p3-unit", default="")
    parser.add_argument("--p3-copy", default="")

    parser.add_argument("--m1-kicker", default="")
    parser.add_argument("--m1-main", default="")
    parser.add_argument("--m1-sub", default="")
    parser.add_argument("--m2-kicker", default="")
    parser.add_argument("--m2-main", default="")
    parser.add_argument("--m2-sub", default="")
    parser.add_argument("--m3-kicker", default="")
    parser.add_argument("--m3-main", default="")
    parser.add_argument("--m3-sub", default="")
    parser.add_argument("--m4-kicker", default="")
    parser.add_argument("--m4-main", default="")
    parser.add_argument("--m4-sub", default="")

    parser.add_argument("--out", required=True)
    parser.add_argument("--keep-html", action="store_true", help="保留调试用临时 HTML")
    args = parser.parse_args()

    if args.mode == "hero":
        content_block = hero_block(args)
    elif args.mode == "people":
        content_block = people_block(args)
    else:
        content_block = structure_block(args)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = render_template(template, {
        "EYEBROW": args.eyebrow,
        "TITLE": args.title,
        "SUBTITLE": args.subtitle,
        "CONTENT_BLOCK": content_block,
        "FOOTER_NOTE": args.footer_note,
    })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 800, "height": 1000}, device_scale_factor=2)
        page.goto(f"file://{tmp_html}", wait_until="networkidle")
        # Wait for local Chinese font and layout to settle before screenshot.
        try:
            font_ok = page.evaluate("document.fonts && document.fonts.ready ? document.fonts.ready.then(() => document.fonts.check('40px \"WenQuanYi Zen Hei\"', '中文测试美国AI')) : true")
            if font_ok is False:
                raise RuntimeError('Chinese font WenQuanYi Zen Hei failed to load; aborting screenshot to avoid tofu boxes')
        except Exception as exc:
            raise RuntimeError(f'Chinese font readiness check failed: {exc}') from exc
        page.wait_for_timeout(300)
        full_height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": 800, "height": full_height})
        page.screenshot(path=str(out), full_page=False)
        browser.close()

    if not args.keep_html and tmp_html.exists():
        tmp_html.unlink()

    print(out)


if __name__ == "__main__":
    main()
