#!/usr/bin/env python3
"""共享图位注入模块（single source of truth）。

替代 format.py / inject_body_images.py / publish_pipe.py 三处分散的实现。
任何对图位逻辑的修改，只能改这里。

公开 API:
    build_img_tag(src) -> str                       # 生成微信 inline-style <img>
    resolve_image(name, search_paths) -> Path|None  # 在候选路径里找图片
    inject_markers(html_or_md, search_paths,        # 替换 <!-- img:filename --> 标记
                   copy_to=None, mode='html')
    inject_by_position(html, image_files)           # 按 h2 顺序插入
    inject(text, search_paths, extra_files=None,    # 主入口：先尝试 marker，无 marker
           copy_to=None, fallback_position=True,    # 且有 extra_files 时按位置插入
           mode='html')

返回结果一律带 stats（dict）：
    {'replaced': int, 'missing': int, 'position_inserted': int, 'missing_files': [str]}
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


IMG_MARKER_RE = re.compile(r"<!--\s*img:\s*(.+?)\s*-->")
H2_RE = re.compile(r"<h2[^>]*>")
P_RE = re.compile(r"<p[^>]*>")
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


@dataclass
class InjectStats:
    replaced: int = 0
    missing: int = 0
    position_inserted: int = 0
    missing_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "replaced": self.replaced,
            "missing": self.missing,
            "position_inserted": self.position_inserted,
            "missing_files": list(self.missing_files),
        }


def build_img_tag(src: str, *, mode: str = "html") -> str:
    """生成微信兼容的图片节点。

    mode='html'  → <section><img/></section>（用于 article.html 注入）
    mode='md'    → ![img](src)（用于 markdown 阶段注入，由 markdown 引擎再渲染）
    """
    if mode == "md":
        return f"![img]({src})"
    return (
        f'\n<section style="text-align:center;margin:24px 0 16px;">'
        f'<img src="{src}" style="width:100%;border-radius:6px;display:block;" />'
        f"</section>\n"
    )


def resolve_image(name: str, search_paths: Iterable[Path]) -> Optional[Path]:
    """在候选路径中查找图片。

    name 可以是文件名、相对路径或绝对路径。
    返回第一个存在且是文件的 Path，找不到则 None。
    """
    name = (name or "").strip()
    if not name:
        return None
    # 1) 绝对路径
    p = Path(name)
    if p.is_absolute() and p.exists() and p.is_file():
        return p
    # 2) 候选目录
    for root in search_paths:
        try:
            root_path = Path(root)
        except TypeError:
            continue
        cand = root_path / name
        if cand.exists() and cand.is_file():
            return cand
        # 也允许只用 basename 匹配
        cand2 = root_path / Path(name).name
        if cand2.exists() and cand2.is_file():
            return cand2
    # 3) 相对当前工作目录
    if p.exists() and p.is_file():
        return p
    return None


def _copy_into(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.resolve() != src.resolve() and not dst.exists():
        shutil.copy2(str(src), str(dst))
    return dst


def inject_markers(
    text: str,
    search_paths: Iterable[Path],
    *,
    copy_to: Optional[Path] = None,
    mode: str = "html",
    src_prefix: str = "images/",
    stats: Optional[InjectStats] = None,
) -> tuple[str, InjectStats]:
    """替换 text 中所有 <!-- img:filename --> 标记。

    - search_paths: 用于定位实际文件
    - copy_to: 若提供，找到的图片会被复制到该目录（一般是 output/images/）
    - mode: 'html' 或 'md'
    - src_prefix: 生成的 src 路径前缀（默认 images/）
    - stats: 复用已有的 stats，否则新建
    """
    stats = stats or InjectStats()

    def replacer(m: re.Match) -> str:
        filename = m.group(1).strip()
        src = resolve_image(filename, search_paths)
        if src is None:
            stats.missing += 1
            stats.missing_files.append(filename)
            return m.group(0)  # 保留原标记
        if copy_to is not None:
            _copy_into(src, copy_to)
            tag_src = f"{src_prefix}{src.name}"
        else:
            tag_src = str(src)
        stats.replaced += 1
        return build_img_tag(tag_src, mode=mode)

    new_text = IMG_MARKER_RE.sub(replacer, text)
    return new_text, stats


def inject_by_position(
    html: str,
    image_files: list[str],
    *,
    src_prefix: str = "images/",
    stats: Optional[InjectStats] = None,
) -> tuple[str, InjectStats]:
    """按 h2 标题顺序在每个 h2 前插入图片。

    若 h2 不够，回退到每隔 3 个段落插入一张；再不够则追加到文末。
    """
    stats = stats or InjectStats()
    if not image_files:
        return html, stats

    positions = [m.start() for m in H2_RE.finditer(html)]
    if not positions:
        p_positions = [m.start() for m in P_RE.finditer(html)]
        positions = p_positions[2::3]

    # 从后往前插入避免偏移
    for i, name in enumerate(reversed(image_files)):
        idx = len(positions) - 1 - i
        tag = build_img_tag(f"{src_prefix}{Path(name).name}")
        if idx < 0:
            html += tag
        else:
            pos = positions[idx]
            html = html[:pos] + tag + html[pos:]
        stats.position_inserted += 1
    return html, stats


def inject(
    text: str,
    search_paths: Iterable[Path],
    *,
    extra_files: Optional[list[Path]] = None,
    copy_to: Optional[Path] = None,
    fallback_position: bool = True,
    mode: str = "html",
    src_prefix: str = "images/",
) -> tuple[str, InjectStats]:
    """主入口。先尝试 marker 替换；如果没有 marker 且 extra_files 非空，
    且 fallback_position=True，则按 h2 位置依次插入 extra_files。

    extra_files：调用方在命令行传的 --images 文件路径列表（要先存在），
                它们会被先复制到 copy_to，再按 basename 引用。
    """
    stats = InjectStats()
    search_paths = list(search_paths)

    # 先把 extra_files 预复制并入到 search_paths
    extra_names: list[str] = []
    if extra_files:
        for raw in extra_files:
            p = Path(raw)
            if not p.exists():
                stats.missing += 1
                stats.missing_files.append(str(raw))
                continue
            if copy_to is not None:
                _copy_into(p, copy_to)
                extra_names.append(p.name)
            else:
                extra_names.append(str(p))
        if copy_to is not None and copy_to not in search_paths:
            search_paths.append(copy_to)

    # 标记替换
    has_marker = bool(IMG_MARKER_RE.search(text))
    if has_marker:
        text, stats = inject_markers(
            text, search_paths,
            copy_to=copy_to, mode=mode, src_prefix=src_prefix, stats=stats,
        )

    # 没有 marker 且有命令行图：按位置插入
    if not has_marker and extra_names and fallback_position and mode == "html":
        text, stats = inject_by_position(
            text, extra_names, src_prefix=src_prefix, stats=stats,
        )

    return text, stats


def format_stats(stats: InjectStats, *, prefix: str = "  ") -> str:
    """生成给 CLI 打印的统计字符串。"""
    lines = []
    if stats.replaced:
        lines.append(f"{prefix}✓ 标记替换: {stats.replaced} 处")
    if stats.position_inserted:
        lines.append(f"{prefix}✓ 按位置注入: {stats.position_inserted} 张")
    if stats.missing:
        lines.append(f"{prefix}⚠ 找不到图片: {stats.missing} 个 → {', '.join(stats.missing_files)}")
    return "\n".join(lines) if lines else f"{prefix}(无图位需要处理)"
