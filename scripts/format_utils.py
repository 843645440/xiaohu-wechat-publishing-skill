#!/usr/bin/env python3
"""format.py 的纯函数集合（无副作用、无 IO、无全局状态）。

从 format.py 抽出，目的是让它们可以被单元测试直接覆盖，而不需要加载整个
1800 行的排版引擎。这里只放最安全的纯函数；涉及样式注入、HTML 字符串替换、
文件读写的逻辑继续留在 format.py。

公开 API：
    count_words(text) -> int                       中英混合字数统计
    extract_title(content, filepath) -> str        frontmatter/H1/文件名三路提取
    strip_frontmatter(content) -> str              剥 YAML frontmatter
    hex_to_rgb(hex_color) -> (r, g, b)             #RRGGBB 转 RGB 元组
"""

from __future__ import annotations

import re
from pathlib import Path


def count_words(text: str) -> int:
    """统计中文文章字数（中文字符 + 英文单词）"""
    clean = re.sub(r"[#*`\[\]()!>|{}_~\-]", "", text)
    clean = re.sub(r"\n+", "\n", clean)
    chinese = len(re.findall(r"[\u4e00-\u9fff]", clean))
    english = len(re.findall(r"[a-zA-Z]+", clean))
    return chinese + english


def extract_title(content: str, filepath: Path) -> str:
    """从内容或文件名提取标题"""
    # 从 frontmatter 提取
    fm = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm:
        for line in fm.group(1).split("\n"):
            if line.startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"').strip("'")
    # 从 H1 提取
    h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1:
        return h1.group(1).strip()
    # 从文件名提取
    name = filepath.stem
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", name)
    name = re.sub(r"-(公众号|小红书|微博)$", "", name)
    return name or filepath.stem


def strip_frontmatter(content: str) -> str:
    """去掉 YAML frontmatter"""
    return re.sub(r"^---\n.*?\n---\n*", "", content, flags=re.DOTALL)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """将 #RRGGBB 转为 (r, g, b) 元组"""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
