# 轻量视觉生成流程

> 只读本页即可。不要加载完整视觉风格库、人物资产说明、旧模板、`.archive/`，也不要做识图审核。

## 必交产物

```text
title-card.json
cover.png
visual-meta.json
body-1.png / body-2.png  # 可选，正文图失败可省略
```

## 封面

- 只用 `title-card.json` 的 `cover_title`、`cover_subtitle`、`highlight`。
- 不塞完整长标题，不加底部三段分类小字。
- 文案按视觉宽度控制：汉字约 1，英文/数字约 0.5。
- 建议宽度：`cover_title` ≤ 7，`cover_subtitle` ≤ 12，`highlight` ≤ 6。
- 最大宽度：`cover_title` ≤ 9，`cover_subtitle` ≤ 15，`highlight` ≤ 8。
- 人物图、裁切、版式、随机选择都由 `render_editorial_cover.py` 内部处理；常规任务不要读取或选择预设。

最简命令：

```bash
python3 scripts/run.py render_editorial_cover.py \
  --account-style xiaocong \
  --article-title "CSDN上线GLM5.2 Coding Plan，海外版贵两倍多" \
  --cover-title "GLM5.2" \
  --cover-subtitle "CSDN上线Coding Plan" \
  --highlight "49元起" \
  --out /abs/job/cover.png
```

自动预设选择规则在脚本内部：`账号 + 月份 + 文章标题 + 封面字段` 稳定伪随机。不要读历史图，不要检查图片相似度，不要让 agent 识图。

## 正文图

正文图按需生成，默认 0-1 张，信息密度高才 2 张。能用表格、列表、引用讲清楚的，不画图。

需要正文图的情况：

- 数据、指标、趋势：信息图。
- 平台规则、消费、职场、生活场景：场景图。
- A/B 对比、前后变化：对比图。
- 工具流程、产业链、工作流：流程图。

不需要正文图的情况：

- 纯观点、短列表、简单解释。
- 文章已经有表格能讲清楚。
- 生成图只会重复正文信息。

## 正文图 Prompt 模板

每张图只选一种类型，控制在 1024x576。

```text
TYPE: infographic | editorial scene | comparison visual | flow map
SUBJECT: article-specific topic
KEY POINTS: 2-4 concrete facts or nodes
STYLE: clean editorial, restrained, readable
TEXT: no text, or max 1-2 short Chinese keywords
NEGATIVE: no watermark, no dense Chinese text, no logos, no fake UI
SIZE: 1024x576
```

## visual-meta.json

只做轻量运行记录，不做长期防重，不引出额外审核。

```json
{
  "title_card": {
    "article_title": "文章 H1",
    "cover_title": "封面主标题",
    "cover_subtitle": "封面副标题",
    "highlight": "高亮词"
  },
  "cover": {
    "type": "magazine-persona-cover",
    "preset": "auto"
  },
  "body_images": [
    {
      "file": "body-1.png",
      "type": "infographic | scene | comparison | flow",
      "subject": "图片服务的具体段落观点"
    }
  ]
}
```

## 失败容错

- 封面失败：报告“封面失败，需后台手动补封面”，不要继续尝试复杂视觉修复。
- 正文图失败：删除对应 `<!-- img:... -->` marker，不传该图，报告说明。
- 不做 OCR、识图、相似度检查或人工视觉评分；这些不适合无视觉能力 agent，性价比低。
