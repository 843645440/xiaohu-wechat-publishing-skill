"""高风险关键词软扫描（check_high_risk）+ JSON 加载回归测试。

覆盖：命中各词；note 拼进 snippet；JSON 缺失回退；返回结构向后兼容。
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from publish_history import check_high_risk, _load_high_risk_keywords


class HighRiskLoadTests(unittest.TestCase):
    """JSON 加载 + 回退。"""

    def test_loads_from_json(self):
        kws, notes = _load_high_risk_keywords()
        # 核心词必须在
        self.assertIn("降息", kws)
        self.assertIn("抄底", kws)
        self.assertIn("地缘", kws)
        # "大盘" 带 note
        self.assertIn("大盘", notes)

    def test_returns_list_and_dict_types(self):
        kws, notes = _load_high_risk_keywords()
        self.assertIsInstance(kws, list)
        self.assertIsInstance(notes, dict)


class HighRiskScanHitTests(unittest.TestCase):
    """命中行为。"""

    def test_flags_multiple_keywords(self):
        hits = check_high_risk("央行可能降息，建议抄底。")
        kws = {kw for _ln, kw, _sn in hits}
        self.assertIn("降息", kws)
        self.assertIn("抄底", kws)

    def test_line_number_correct(self):
        hits = check_high_risk("第一行正常\n第二行提到领导人\n第三行")
        # 命中应在第 2 行
        self.assertEqual(hits[0][0], 2)

    def test_dedup_per_keyword(self):
        # 同一关键词多次出现只报一次
        hits = check_high_risk("降息。再说一次降息。")
        kws = [kw for _ln, kw, _sn in hits]
        self.assertEqual(kws.count("降息"), 1)

    def test_note_appended_to_snippet(self):
        # "大盘" 有 note，应拼进 snippet
        hits = check_high_risk("今天大盘鸡很好吃。")
        # 三元组结构不变
        _ln, kw, sn = hits[0]
        self.assertEqual(kw, "大盘")
        self.assertIn("易误报", sn)

    def test_clean_text_no_hits(self):
        self.assertEqual(check_high_risk("一篇讲 AI 工具如何改变设计师日常的文章"), [])

    def test_three_tuple_structure_preserved(self):
        """向后兼容：返回值仍是 (line_no, keyword, snippet) 三元组。"""
        hits = check_high_risk("提到降息。")
        self.assertEqual(len(hits[0]), 3)


class HighRiskFallbackTests(unittest.TestCase):
    """关键词缺失时回退到内置最小集（通过显式传 keywords 模拟）。"""

    def test_explicit_keywords_override(self):
        # 显式传 keywords 时使用它，不读文件
        hits = check_high_risk("命中自定义词。", keywords=["自定义词"])
        kws = [kw for _ln, kw, _sn in hits]
        self.assertIn("自定义词", kws)

    def test_empty_keywords_no_hits(self):
        self.assertEqual(check_high_risk("降息抄底", keywords=[]), [])


if __name__ == "__main__":
    unittest.main()
