import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PublishValidationTests(unittest.TestCase):
    def test_process_img_markers_keeps_markers_for_publish_stage(self):
        from format import process_img_markers

        sample = "前文\n\n<!-- img:hero.png -->\n\n后文"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = process_img_markers(sample, root, root / "out")

        self.assertIn("<!-- img:hero.png -->", result)

    def test_rejects_account_name_as_title(self):
        from publish_pipe import validate_publish_ready

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            article_dir = root / "article"
            article_dir.mkdir()
            cover = root / "cover.png"
            cover.write_bytes(b"fake")

            result = validate_publish_ready(
                html="<h1>熵增时刻</h1><p>正文</p>",
                article_dir=article_dir,
                cover_path=cover,
                title="熵增时刻",
                accounts=[("xiaocong", "wx123456", "secret", "熵增时刻")],
                inject_missing=0,
            )

        self.assertFalse(result.ok)
        self.assertTrue(any("账号名" in issue for issue in result.issues))

    def test_rejects_leftover_markers_and_missing_local_images(self):
        from publish_pipe import validate_publish_ready

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            article_dir = root / "article"
            article_dir.mkdir()
            cover = root / "cover.png"
            cover.write_bytes(b"fake")

            result = validate_publish_ready(
                html='<h1>正式标题</h1><p><!-- img:hero.png --></p><img src="images/missing.png">',
                article_dir=article_dir,
                cover_path=cover,
                title="正式标题",
                accounts=[("xiaocong", "wx123456", "secret", "熵增时刻")],
                inject_missing=1,
            )

        self.assertFalse(result.ok)
        self.assertTrue(any("marker" in issue for issue in result.issues))
        self.assertTrue(any("图片文件不存在" in issue for issue in result.issues))


class DoctorModeTests(unittest.TestCase):
    def test_format_mode_does_not_require_accounts(self):
        from doctor import mode_requires_accounts

        self.assertFalse(mode_requires_accounts("format"))
        self.assertTrue(mode_requires_accounts("publish"))
        self.assertTrue(mode_requires_accounts("all"))


class HighRiskScanTests(unittest.TestCase):
    def test_flags_high_risk_keyword(self):
        from publish_history import check_high_risk

        hits = check_high_risk("第一行正常\n央行可能降息，建议抄底\n结尾")

        kws = {kw for _ln, kw, _sn in hits}
        self.assertIn("降息", kws)
        self.assertIn("抄底", kws)
        self.assertEqual(hits[0][0], 2)  # line number

    def test_clean_text_has_no_hits(self):
        from publish_history import check_high_risk

        self.assertEqual(check_high_risk("一篇讲AI工具如何改变设计师日常的文章"), [])


if __name__ == "__main__":
    unittest.main()
