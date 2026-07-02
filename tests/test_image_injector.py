"""图片注入（image_injector）回归测试。

覆盖：marker 解析成功 / 未解析保留 / 按位置插入 / extra_files 预复制 / 路径查找。
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from image_injector import (
    inject,
    inject_markers,
    resolve_image,
    build_img_tag,
)


def _make_image(dir_path: Path, name: str) -> Path:
    p = dir_path / name
    p.write_bytes(b"\x89PNG fake image")  # 占位文件，注入只检查存在性
    return p


class ResolveImageTests(unittest.TestCase):
    def test_absolute_path(self):
        with tempfile.TemporaryDirectory() as td:
            img = _make_image(Path(td), "a.png")
            self.assertEqual(resolve_image(str(img), []), img)

    def test_in_search_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_image(root, "b.png")
            self.assertEqual(resolve_image("b.png", [root]), root / "b.png")

    def test_basename_match(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_image(root, "c.png")
            self.assertEqual(resolve_image("sub/c.png", [root]), root / "c.png")

    def test_not_found_returns_none(self):
        self.assertIsNone(resolve_image("nope.png", [Path("/nonexistent")]))


class InjectMarkersTests(unittest.TestCase):
    def test_replaces_marker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_image(root, "hero.png")
            html = '<p>x</p>\n<!-- img: hero.png -->\n<p>y</p>'
            out, stats = inject_markers(html, [root])
            self.assertEqual(stats.replaced, 1)
            self.assertEqual(stats.missing, 0)
            self.assertIn("<img", out)
            self.assertNotIn("<!-- img:", out)

    def test_preserves_unresolved_marker(self):
        # 图片不存在时，marker 保留，记入 missing
        html = "<p>x</p>\n<!-- img: missing.png -->"
        out, stats = inject_markers(html, [Path("/nonexistent")])
        self.assertEqual(stats.missing, 1)
        self.assertIn("<!-- img: missing.png -->", out)
        self.assertNotIn("<img", out)

    def test_copy_to_copies_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = _make_image(root, "hero.png")
            dst_dir = Path(td) / "out" / "images"
            html = "<p>x</p>\n<!-- img: hero.png -->"
            out, stats = inject_markers(html, [root], copy_to=dst_dir)
            self.assertTrue((dst_dir / "hero.png").exists())
            self.assertIn('src="images/hero.png"', out)


class InjectByPositionTests(unittest.TestCase):
    def test_inserts_by_h2(self):
        # 无 marker，有 extra_files，按 h2 位置插入
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copy_to = root / "out"
            copy_to.mkdir()
            html = "<h2>章节一</h2><p>内容</p><h2>章节二</h2><p>内容</p>"
            out, stats = inject(
                html, [root],
                extra_files=[_make_image(root, "a.png")],
                copy_to=copy_to,
            )
            self.assertEqual(stats.position_inserted, 1)
            self.assertIn("<img", out)


class BuildImgTagTests(unittest.TestCase):
    def test_html_mode(self):
        tag = build_img_tag("images/x.png")
        self.assertIn("<img", tag)
        self.assertIn('src="images/x.png"', tag)

    def test_md_mode(self):
        tag = build_img_tag("images/x.png", mode="md")
        self.assertEqual(tag, "![img](images/x.png)")


if __name__ == "__main__":
    unittest.main()
