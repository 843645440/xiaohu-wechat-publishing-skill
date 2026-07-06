from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class LowQualitySimilarityTests(unittest.TestCase):
    def test_signature_detects_fixed_quality_template_headings(self):
        from publish_history import build_content_signature

        md = """# 正式标题

## 事实底座
这里是事实。

## 背景解释
这里是背景。

## 普通人影响
这里是影响。

## 中国变量
这里是结论。
"""

        sig = build_content_signature(md, title="正式标题")

        self.assertEqual(sig["structure_archetype"], "fixed_quality_template")
        self.assertGreaterEqual(sig["generic_heading_count"], 3)

    def test_same_account_recent_repeated_signature_warns(self):
        from publish_history import build_content_signature, check_low_quality_similarity

        md = """# 不是工具变了，是工作流变了

开头先讲一个具体事实。

## 为什么这次变化值得看
第一段。

## 普通人最关心什么
第二段。

## 接下来怎么判断
第三段。

- 清单一
- 清单二
"""
        sig = build_content_signature(md, title="不是工具变了，是工作流变了")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        history = [{
            "ts": ts,
            "account": "xiaocong",
            "title": "不是模型变了，是应用层变了",
            "extra": {"content_signature": sig},
        }]

        warnings = check_low_quality_similarity(sig, accounts=["xiaocong"], history=history)

        self.assertTrue(warnings)
        self.assertIn("同账号", warnings[0]["reason"])

    def test_other_account_history_is_ignored(self):
        from publish_history import build_content_signature, check_low_quality_similarity

        md = """# 平台规则变了，小商家要看懂

一个订单变化开始。

## 为什么这次变化值得看
第一段。

## 普通人最关心什么
第二段。

## 接下来怎么判断
第三段。
"""
        sig = build_content_signature(md, title="平台规则变了，小商家要看懂")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        history = [{
            "ts": ts,
            "account": "yeluzi",
            "title": "平台规则变了，小商家要看懂",
            "extra": {"content_signature": sig},
        }]

        warnings = check_low_quality_similarity(sig, accounts=["xiaocong"], history=history)

        self.assertEqual(warnings, [])

    def test_visual_meta_repetition_warns_without_image_recognition(self):
        from publish_history import build_content_signature, check_low_quality_similarity

        md = """# 一个新标题

## 第一节
正文。

## 第二节
正文。
"""
        visual_meta = {
            "cover": {
                "archetype": "结构地图型",
                "layout": "left-title-right-map",
                "subject": "AI 工具工作流",
                "prompt_key": "same-cover-prompt",
            },
            "body_images": [
                {
                    "file": "body-1.png",
                    "type": "structure-map",
                    "style": "infographic-blueprint",
                    "prompt_key": "same-body-prompt",
                }
            ],
        }
        sig = build_content_signature(md, title="一个新标题", visual_meta=visual_meta)
        old = build_content_signature(md, title="另一个标题", visual_meta=visual_meta)
        old["structure_archetype"] = "different"
        old["title_pattern"] = "different"
        old["opening_pattern"] = "different"
        old["heading_signature"] = ["different"]
        old["element_sequence_key"] = "different"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        history = [{
            "ts": ts,
            "account": "xiaocong",
            "title": "另一个标题",
            "extra": {"content_signature": old},
        }]

        warnings = check_low_quality_similarity(sig, accounts=["xiaocong"], history=history)

        self.assertTrue(warnings)
        self.assertIn("封面", warnings[0]["detail"])
        self.assertIn("正文图", warnings[0]["detail"])


if __name__ == "__main__":
    unittest.main()
