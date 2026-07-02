"""format_utils 纯函数 + format.py CJK 函数回归测试。

format_utils: count_words / extract_title / strip_frontmatter / hex_to_rgb
format.py: fix_cjk_spacing / fix_cjk_bold_punctuation（留在原文件，直接 import 测）
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from format_utils import count_words, extract_title, strip_frontmatter, hex_to_rgb
from format import fix_cjk_spacing, fix_cjk_bold_punctuation


class CountWordsTests(unittest.TestCase):
    def test_pure_chinese(self):
        # 5 个中文字符
        self.assertEqual(count_words("你好世界啊"), 5)

    def test_pure_english(self):
        # 2 个英文单词
        self.assertEqual(count_words("hello world"), 2)

    def test_mixed(self):
        # 4 个中文（你好/世界）+ 1 个英文单词（hello）
        self.assertEqual(count_words("你好 hello 世界"), 5)

    def test_strips_markdown(self):
        # markdown 符号不计入
        self.assertEqual(count_words("**加粗**"), 2)


class ExtractTitleTests(unittest.TestCase):
    def test_from_frontmatter(self):
        content = "---\ntitle: 我的标题\n---\n正文"
        self.assertEqual(extract_title(content, Path("x.md")), "我的标题")

    def test_from_frontmatter_quoted(self):
        content = '---\ntitle: "带引号的标题"\n---\n正文'
        self.assertEqual(extract_title(content, Path("x.md")), "带引号的标题")

    def test_from_h1(self):
        content = "# 一级标题\n正文"
        self.assertEqual(extract_title(content, Path("x.md")), "一级标题")

    def test_from_filename(self):
        content = "正文"
        self.assertEqual(extract_title(content, Path("2026-07-02-我的文章.md")), "我的文章")

    def test_filename_strips_platform_suffix(self):
        content = "正文"
        self.assertEqual(extract_title(content, Path("主题-公众号.md")), "主题")


class StripFrontmatterTests(unittest.TestCase):
    def test_strips_simple(self):
        self.assertEqual(strip_frontmatter("---\na: 1\n---\n正文"), "正文")

    def test_no_frontmatter_unchanged(self):
        self.assertEqual(strip_frontmatter("纯正文"), "纯正文")


class HexToRgbTests(unittest.TestCase):
    def test_standard(self):
        self.assertEqual(hex_to_rgb("#1e3a5f"), (0x1e, 0x3a, 0x5f))

    def test_without_hash(self):
        self.assertEqual(hex_to_rgb("ffffff"), (255, 255, 255))

    def test_black(self):
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))


class CjkSpacingTests(unittest.TestCase):
    def test_inserts_space_between_cjk_and_latin(self):
        self.assertEqual(fix_cjk_spacing("你好hello"), "你好 hello")

    def test_inserts_space_between_cjk_and_digit(self):
        self.assertEqual(fix_cjk_spacing("价格100元"), "价格 100 元")

    def test_skips_inline_code(self):
        # 行内代码内不应插空格
        result = fix_cjk_spacing("用 `python3` 运行")
        self.assertIn("`python3`", result)

    def test_skips_url(self):
        result = fix_cjk_spacing("见 https://example.com/p1")
        self.assertIn("https://example.com/p1", result)

    def test_skips_code_block(self):
        text = "正文\n```\nx=1\n```\n结束"
        result = fix_cjk_spacing(text)
        # 代码块内容不变
        self.assertIn("x=1", result)


class CjkBoldPunctuationTests(unittest.TestCase):
    def test_moves_comma_out_of_bold(self):
        self.assertEqual(fix_cjk_bold_punctuation("**文字，**"), "**文字**，")

    def test_moves_period_out_of_bold(self):
        self.assertEqual(fix_cjk_bold_punctuation("**文字。**"), "**文字**。")


if __name__ == "__main__":
    unittest.main()
