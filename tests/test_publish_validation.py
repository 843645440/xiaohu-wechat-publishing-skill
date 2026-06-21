import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PublishValidationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
