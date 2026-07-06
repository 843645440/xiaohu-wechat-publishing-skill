---
name: xiaohu-wechat-publishing
description: |
  Use when working with WeChat Official Account: topic planning, lightweight writing, AI-flavor reduction, cover/body visuals, formatting, and draft-box publishing. Triggers: 写公众号, 微信排版, 公众号文章, 推草稿箱, 发公众号, 熵增时刻, 思想的野路子丶, or packaging an article for WeChat.
version: 5.1.0
author: Hermes curator
license: MIT
metadata:
  hermes:
    tags: [wechat, mp, article, pipeline, formatting, cover, publish, xiaohu]
---

# 小虎公众号轻量生产管线

这是唯一主 skill。目标不是每篇都做成深度专栏，而是稳定批量产出：避开明显风控，有一点有用信息，表达清楚，读起来不像低质 AIGC。

## 默认原则

- 只加载 `xiaohu-wechat-publishing`，不要额外加载 humanizer / baoyu 相关 skill。
- 主流程按阶段读取少量内部文件，不全量加载 references。
- 正文、封面、图片里都不要出现任何 AI 身份披露；发布脚本会硬拦截。
- 凭据只从 `~/.hermes/.env` 读取；不要把 app_id/app_secret 写进仓库文件。
- 只推公众号草稿箱，不自动群发；最终发布由真人复核。

## 必读文件

按阶段读，不要提前读无关文件：

1. 写作前读 `prompts/quality-and-risk.md` 和 `prompts/markdown-elements.md`。
2. 初稿完成后必须读 `references/humanizer-runtime.md` 做去 AI 味。
3. 生成封面/正文图前必须读 `references/visual-generation-light.md`。
4. 去 AI 味卡住时才读 `prompts/examples.md`。

不要读取旧人设、完整视觉风格库、复杂结构防重或长篇排障材料。

## 轻量主流程

1. 明确账号和任务：`xiaocong` 偏科技/产业/AI，`yeluzi` 偏民生/消费/职场/平台规则。
2. 找安全选题：避开政治、敏感社会议题、财经预测、投资建议、未经证实爆料。
3. 查近期历史：只看同账号最近标题和文章大意，避免写同一件事或同一大意。
4. 写初稿：1500-3000 字，至少 2 个信息源，重要事实尽量 3 个源；不规定固定结构。
5. 去 AI 味：读 `references/humanizer-runtime.md`，AI 味风险为高时不得发布。
6. 生成视觉：封面必做；正文图进入判断，按文章类型生成 0-2 张。
7. 排版和发布：先 dry-run，通过后推草稿箱。
8. 归档：只记录标题和 100-200 字文章大意，供后续防重。

## 写作要求

- 不写单篇新闻改写；至少整合 2 个独立来源。
- 开头 3 段内说清楚：发生了什么，为什么现在值得看。
- 每篇至少给读者 1 个有用信息点：数据、背景、对比、避坑、操作建议、行业变化之一。
- 小标题自然生成，不用模板标题。
- 不强制固定结构或固定报告角度。
- 如果安全题不足，停止并说明“今天不适合自动生成草稿”，不要硬写。

## 去 AI 味硬规则

每篇正文写完后都必须执行去 AI 味。只在这个阶段读取 `references/humanizer-runtime.md`。

去 AI 味不是可选润色，而是进推荐池前的基本门槛。终稿必须自评：

```text
AI 味风险：低 / 中 / 高
空话密度：低 / 中 / 高
口语自然度：低 / 中 / 高
是否需要重写：是 / 否
```

若 AI 味风险为高，重写或继续去 AI 味，不得进入排版发布。

## 视觉要求

- 封面必生成 `cover.png`，保持现有封面流程和账号气质。
- 正文图必须进入判断阶段，但数量可以是 0、1 或 2 张。
- 正文图只走轻量路径：信息图、场景图、对比图、流程/结构图。
- 生成前在 job 目录写 `visual-meta.json`，记录本次 prompt 意图，方便人工复盘；不再把视觉元数据写入长期防重历史。
- 图片失败不阻断主流程：封面失败可跳过封面参数，正文图失败删除 marker，最终报告说明“配图失败，已跳过”。

## 运行命令

所有脚本通过统一入口运行：

```bash
python3 scripts/run.py doctor.py --mode format
python3 scripts/run.py doctor.py --mode publish
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
```

Cron 自动任务推荐：

```bash
python3 scripts/run.py publish_pipe.py \
  --input /abs/job/article.md \
  --cover /abs/job/cover.png \
  --job-dir /abs/job \
  --account xiaocong \
  --fail-on-low-quality-warning \
  --dry-run
```

正式推送去掉 `--dry-run`。

## 发布前硬校验

`publish_pipe.py` 和 `validate_publish_ready` 负责硬校验：

- Markdown 不含 AI 身份披露或“利益相关”声明。
- `article.html` 存在。
- H1 / `--title` 是真实标题，不是账号名。
- 没有残留 `<!-- img:... -->` marker。
- 图位注入没有 missing。
- 封面存在，或明确按配图失败容错跳过。
- HTML 中本地图片文件存在。
- 正式发布时账号凭据齐全。

高风险关键词只 warning，不阻断；人工确认是否需要换题或软化切口。

## 轻量防重

发布脚本只保存标题和文章大意，不保存全文、不保存结构签名、不保存视觉历史。

防重逻辑只比较同账号近期：

- 标题是否高度相似。
- 文章大意是否高度相似。

命中时，cron 使用 `--fail-on-low-quality-warning` 停止发布；人工临时发布可只看 warning。

## 工作区产物

默认工作区：

```text
~/.hermes/workspaces/wechat/
  jobs/
  cache/tokens/
  manual-format/
  publish-history.jsonl
  publish-history.md
```

单篇 job 目录建议包含：

```text
article.md
cover.png
visual-meta.json
body-1.png / body-2.png  # 如有
format/
```

## Cron 提示词

`cron-prompts/` 是维护副本，真实运行配置仍需同步到 Hermes cron。Cron prompt 只保留任务差异和执行顺序，不复制长规则。

最终报告只需要：

```text
标题：
文章大意：
为什么选这个题：
来源数量：
是否避开敏感题：
是否与近期大意重复：
去 AI 味是否完成：
封面/正文图结果：
dry-run/草稿箱结果：
产物路径：
```

不要添加额外的固定结构分析字段。

## 排版和发布路径

已有 Markdown：

```bash
python3 scripts/run.py publish_pipe.py \
  --input /abs/path/article.md \
  --cover /abs/path/cover.png \
  --job-dir /abs/path/job \
  --account yeluzi \
  --dry-run
```

已有排版 HTML：

```bash
python3 scripts/run.py publish_pipe.py \
  --dir /abs/path/job \
  --cover /abs/path/cover.png \
  --account yeluzi
```

`--input --job-dir` 是 cron 和日常最简路径。

## 失败处理

- 环境问题：跑 `python3 scripts/run.py doctor.py --mode format`；发布问题跑 `--mode publish`。
- 图片缺失：检查 Markdown marker、`--images`、job 目录图片和 `article.html`。
- 标题错误：检查 Markdown 第一个 `#` 或 `--title`。
- Cron 没推草稿箱：看 job 目录是否有产物、`publish-history.jsonl` 是否新增记录、`~/.hermes/cron/output/` 最新日志是否真的调用了 `publish_pipe.py`。

## Output Contract

完成任务后报告：

- 产物路径。
- dry-run / 草稿箱结果。
- 是否写入历史。
- 是否有 warning。
- 如果没能发布，先说失败原因，再说下一步。
