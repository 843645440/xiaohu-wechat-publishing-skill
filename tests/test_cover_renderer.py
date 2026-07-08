import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class CoverRendererTests(unittest.TestCase):
    def test_visual_width_counts_ascii_lighter_than_chinese(self):
        from render_editorial_cover import visual_width

        self.assertLess(visual_width("GLM5.2"), visual_width("楼下超市"))
        self.assertLessEqual(visual_width("CSDN上线Coding Plan"), 15)

    def test_fit_visual_text_truncates_over_budget(self):
        from render_editorial_cover import fit_visual_text, visual_width

        value = fit_visual_text("CSDN上线GLM5.2 Coding Plan 海外版贵两倍多", 15)

        self.assertTrue(value.endswith("…"))
        self.assertLessEqual(visual_width(value), 15)

    def test_title_size_keeps_four_chinese_chars_from_overblowing(self):
        from render_editorial_cover import title_size_class

        self.assertEqual(title_size_class("GLM5.2"), "title-short")
        self.assertEqual(title_size_class("楼下超市"), "title-medium")

    def test_cover_presets_load_and_select_stably(self):
        from render_editorial_cover import load_presets, select_preset

        presets = load_presets()
        seed = "xiaocong:article:GLM5.2:CSDN上线Coding Plan"
        first = select_preset(presets, "auto", "xiaocong", "2026-07", seed)
        second = select_preset(presets, "auto", "xiaocong", "2026-07", seed)

        self.assertGreaterEqual(len(presets), 3)
        self.assertEqual(first[0], second[0])
        self.assertIn("variant", first[1])
        self.assertIn("persona", first[1])

    def test_unknown_cover_preset_fails_fast(self):
        from render_editorial_cover import load_presets, select_preset

        with self.assertRaises(SystemExit):
            select_preset(load_presets(), "missing-preset", "xiaocong", "2026-07", "seed")


if __name__ == "__main__":
    unittest.main()
