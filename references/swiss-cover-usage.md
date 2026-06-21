# Swiss Minimal 封面使用指南

## 快速命令

```bash
# 熵增时刻账号
python scripts/render_cover_swiss.py \
  --brand '熵增时刻 · ENTROPY' \
  --title-line1 '你为什么' \
  --title-hl '总焦虑？' \
  --subtitle '不是脆弱，是不甘平庸的信号' \
  --issue 'VOL.05 / 2026' \
  --topic '成长 · 内耗 · 野心' \
  --out /path/to/cover-xiaocong.png

# 思想的野路子账号
python scripts/render_cover_swiss.py \
  --brand '思想的野路子丶 · WILD THINKING' \
  --title-line1 '越清醒' \
  --title-hl '越内耗？' \
  --subtitle '真正痛苦的人，往往不是没有能力' \
  --issue 'VOL.05 / 2026' \
  --topic '情绪 · 现实 · 向上' \
  --out /path/to/cover-yeluzi.png
```

## 参数说明

| 参数 | 用途 | 示例 |
|------|------|------|
| `--brand` | 顶部品牌条 | `熵增时刻 · ENTROPY` |
| `--title-line1` | 标题前半（黑字） | `你为什么` |
| `--title-hl` | 红字 hook 短句 | `总焦虑？` |
| `--subtitle` | 副线索（悬念，不给结论） | `不是脆弱，是不甘平庸的信号` |
| `--issue` | 期号 | `VOL.05 / 2026` |
| `--topic` | 标签 | `成长 · 内耗 · 野心` |
| `--out` | 输出路径 | `cover.png` |

## 设计原则

- **标题钩子 ≤ 12 字**：`总焦虑？` / `越内耗？` 这种短句最抓眼球
- **副悬念不给结论**：让读者想点进去看答案
- **红字是视觉锤**：title-hl 用红色高亮，是封面唯一颜色焦点
- **两个账号共用模板**：只换 brand / issue / topic 元信息，风格统一

## 与 publish_pipe.py 配合

生成封面后直接推草稿箱：

```bash
python scripts/publish_pipe.py \
  --input article.md \
  --cover cover-xiaocong.png \
  --account xiaocong \
  --theme terracotta
```