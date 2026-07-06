from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class LowQualitySimilarityTests(unittest.TestCase):
    def test_signature_keeps_only_title_and_summary(self):
        from publish_history import build_content_signature

        md = """# 正式标题

这是一篇讲平台规则变化的文章。它重点说明小商家在退款、客服和订单处理里遇到的新问题。

## 一个具体变化
正文。
"""
        sig = build_content_signature(md, title="正式标题")

        self.assertEqual(sig["schema"], 2)
        self.assertEqual(sig["title"], "正式标题")
        self.assertIn("平台规则变化", sig["summary"])
        self.assertNotIn("structure_archetype", sig)
        self.assertNotIn("cover_meta", sig)

    def test_same_account_recent_summary_warns(self):
        from publish_history import build_content_signature, check_low_quality_similarity

        md = """# 平台退款规则变了，小商家最先感到压力

这篇文章讲平台退款规则变化，小商家在订单处理、售后客服和成本分摊里遇到的新压力。
"""
        sig = build_content_signature(md, title="平台退款规则变了，小商家最先感到压力")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        history = [{
            "ts": ts,
            "account": "yeluzi",
            "title": "平台退款规则变了，小店老板先感到压力",
            "summary": "这篇文章讲平台退款规则变化，小商家在订单处理、售后客服和成本分摊里遇到的新压力。",
        }]

        warnings = check_low_quality_similarity(sig, accounts=["yeluzi"], history=history)

        self.assertTrue(warnings)
        self.assertRegex(warnings[0]["detail"], "标题|文章大意")

    def test_other_account_history_is_ignored(self):
        from publish_history import build_content_signature, check_low_quality_similarity

        sig = build_content_signature(
            "AI 工具进入工单系统，客服流程开始被重新拆分。",
            title="AI 工具进入工单系统",
        )
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        history = [{
            "ts": ts,
            "account": "xiaocong",
            "title": "AI 工具进入工单系统",
            "summary": "AI 工具进入工单系统，客服流程开始被重新拆分。",
        }]

        warnings = check_low_quality_similarity(sig, accounts=["yeluzi"], history=history)

        self.assertEqual(warnings, [])

    def test_record_publish_keeps_minimal_history(self):
        from publish_history import record_publish
        import publish_history
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            original = publish_history.workspace_root
            publish_history.workspace_root = lambda: td
            try:
                path = record_publish(
                    account="xiaocong",
                    title="标题",
                    summary="文章大意",
                    media_id="media123",
                    job_dir="/tmp/job",
                    article_dir="/tmp/article",
                    cover="/tmp/cover.png",
                    app_id="wx-secret",
                )
                line = path.read_text(encoding="utf-8").strip()
            finally:
                publish_history.workspace_root = original

        self.assertIn('"title": "标题"', line)
        self.assertIn('"summary": "文章大意"', line)
        self.assertNotIn("job_dir", line)
        self.assertNotIn("cover", line)


if __name__ == "__main__":
    unittest.main()
