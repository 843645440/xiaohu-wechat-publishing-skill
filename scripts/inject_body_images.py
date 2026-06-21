#!/usr/bin/env python3
"""正文图自动注入工具（兼容入口）。

⚠ 实际逻辑已统一到 scripts/image_injector.py（single source of truth）。
本脚本保留为命令行兼容入口，调用 image_injector.inject()。

用法：
    python3 inject_body_images.py --html <article.html> --images <image_dir>
    python3 inject_body_images.py --html <article.html> --images <img1.png> <img2.png>
"""

import argparse
import sys
from pathlib import Path

from image_injector import inject as inject_images, format_stats


def main():
    parser = argparse.ArgumentParser(description="正文图自动注入（→ image_injector）")
    parser.add_argument("--html", required=True, help="article.html 路径")
    parser.add_argument("--images", nargs="+", required=True,
                        help="图片文件名、文件路径或图片目录")
    parser.add_argument("--mode", choices=["auto", "marker"], default="auto",
                        help="auto=有 marker 就用 marker，没 marker 按 h2 位置插入；marker=只处理 marker")
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(f"错误: HTML 文件不存在 - {html_path}", file=sys.stderr)
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8")
    images_dir = html_path.parent / "images"
    images_dir.mkdir(exist_ok=True)

    # 解析 --images：可以是目录、文件路径混合
    extra_files: list[Path] = []
    search_paths: list[Path] = [images_dir, html_path.parent]
    for raw in args.images:
        p = Path(raw)
        if p.is_dir():
            search_paths.insert(0, p)
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif") and not f.name.startswith("cover"):
                    extra_files.append(f)
        else:
            extra_files.append(p)

    fallback = (args.mode == "auto")
    new_html, stats = inject_images(
        html, search_paths,
        extra_files=extra_files,
        copy_to=images_dir,
        fallback_position=fallback,
        mode="html",
    )

    html_path.write_text(new_html, encoding="utf-8")
    print(format_stats(stats))
    img_count = new_html.count("<img")
    print(f"\n完成! HTML 中共有 {img_count} 个 <img> 标签")
    print(f"输出: {html_path}")
    if stats.missing > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
