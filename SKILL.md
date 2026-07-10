---
name: xiaohu-wechat-publishing
description: |
  Use when working with WeChat Official Account: topic planning, lightweight writing, external humanizer pass, cover/body visuals, formatting, and draft-box publishing. Triggers: 写公众号, 微信排版, 公众号文章, 推草稿箱, 发公众号, 熵增时刻, 思想的野路子丶, or packaging an article for WeChat.
version: 5.3.0
author: Hermes curator
license: MIT
metadata:
  hermes:
    tags: [wechat, mp, article, pipeline, formatting, cover, publish, xiaohu]
---

# 小虎公众号轻量生产管线

这是公众号主 skill。目标不是每篇都做成深度专栏，而是稳定批量产出：避开明显风控，像热点新闻记者一样，用可核实事实提供清楚、可复述的信息增量。去 AI 味统一交给外部 `humanizer` skill，xiaohu 内部不再维护自有去味规则。

## 默认原则

- 必须加载 `xiaohu-wechat-publishing` 和外部 `humanizer` skill；不要加载 baoyu 相关 skill。
- 主流程按阶段读取少量内部文件，不全量加载 references。
- 正文、封面、图片里都不要出现任何 AI 身份披露；发布脚本会硬拦截。
- 凭据只从 `~/.hermes/.env` 读取；不要把 app_id/app_secret 写进仓库文件。
- 只推公众号草稿箱，不自动群发；最终发布由真人复核。

## 必读文件

按阶段读，不要提前读无关文件：

1. 写作前读 `prompts/quality-and-risk.md`、`prompts/title-and-cover.md` 和 `prompts/markdown-elements.md`。
2. 初稿完成后必须使用外部 `humanizer` skill 做去 AI 味，不读取 xiaohu 内部去味文件。
3. 生成封面/正文图前只读 `references/visual-generation-light.md`。

不要读取封面预设池 JSON、旧人设、完整视觉风格库、复杂结构防重、长篇排障材料、`.archive/` 归档内容，或已删除的 xiaohu 内部去味文件。

## 轻量主流程

1. 明确账号和任务：`xiaocong` 偏科技/产业/AI，`yeluzi` 偏民生/消费/职场/平台规则。
2. 找安全选题：避开政治、敏感社会议题、财经预测、投资建议、未经证实爆料。
3. 查近期历史：只看同账号最近标题和文章大意，避免写同一件事或同一大意。
4. 整理事实底稿：在 job 目录写简短的 `source-notes.md`，记录核心新闻点、3-6 条可核实事实及其来源、有效背景/对比、暂不能确认的信息。转载同一原始消息的页面只算 1 个来源。
5. 写初稿：篇幅完全跟信息量走，通常 1000-3500 字，仅在来源足、机制复杂或有多方对比时写到 3500-4500 字；这是参考范围，不是凑字指标。把自己当作热点新闻记者，围绕当篇素材自然组织，不套固定栏目。
6. 删空话：初稿完成后删除重复结论、万能过渡、无事实支撑的感叹，以及删掉后不影响理解的段落。
7. 去 AI 味：调用外部 `humanizer` skill 重写表达，但不得新增、删除或改变关键事实；保存 `article.raw.md`、`article.md` 和 `humanizer-report.md`。AI 味或空话密度为高时不得发布。
8. 标题压缩：基于终稿写 `title-card.json`，输出 `article_title`、`cover_title`、`cover_subtitle`、`highlight`；封面文案按视觉宽度控制，`article.md` 的 H1 使用 `article_title`。
9. 生成视觉：封面必做；封面只吃短封面字段并使用内置封面预设池；正文图进入判断，按文章类型生成 0-2 张。
10. 排版和发布：确认 `source-notes.md` 存在、AI 味与空话密度都不高、关键事实完整后再 dry-run，通过后推草稿箱。
11. 归档：只记录标题和 100-200 字文章大意，供后续防重；`source-notes.md` 只留在当次 job，不进入长期历史。

## 写作要求

- 不写单篇新闻改写；优先使用官方公告、产品页、规则原文、公开数据等一手来源，再用独立来源补充或交叉核对。搜索摘要不算来源。
- 篇幅跟信息量走：短消息短写，复杂事件长写；不要为了达到参考字数扩写空话。
- 像热点新闻记者：抓住新闻点，补充可核实的事实、背景、数字、对比、案例或操作信息；没有可靠来源的场景、反应和引语不要编。
- 每篇必须有读者能复述的信息增量，不只复述消息、改写新闻稿或堆情绪。
- 每个段落至少承担一种作用：提供新事实、解释事实、给出有效对比或帮助读者采取行动。纯过渡和重复总结直接删除。
- 标题必须经过 `prompts/title-and-cover.md` 压缩；强主体文章要在标题中点名公司/平台/产品。
- 小标题自然生成，不用模板标题；不要套固定栏目或统一四段式。
- 最终报告字段只用于任务汇报，不要写成正文提纲或正文小标题。
- 如果安全题不足，停止并说明“今天不适合自动生成草稿”，不要硬写。

## 去 AI 味硬规则

每篇正文写完后都必须执行外部 `humanizer` skill。xiaohu skill 内部不再维护 `references/humanizer-runtime.md` 或去味示例文件。

推荐产物：

```text
article.raw.md          # 初稿
article.md              # humanizer 后终稿
source-notes.md         # 当次事实底稿，不进入长期历史
title-card.json         # 文章标题和封面短文案
humanizer-report.md     # 外部 humanizer 检查与修改摘要
```

外部 humanizer 完成后，终稿必须自评：

```text
AI 味风险：低 / 中 / 高
空话密度：低 / 中 / 高
口语自然度：低 / 中 / 高
关键事实保留：完整 / 有缺失
是否需要重写：是 / 否
```

`humanizer` 只能调整表达和节奏，不得改动数字、日期、主体、引用归属、来源结论或不确定性限定，也不得凭空补充案例和观点。

- AI 味风险为高：继续用外部 `humanizer` skill 重写。
- 空话密度为高：不得发布，先压缩重写。
- 空话密度为中：删除重复和无信息段落后再检查。
- 关键事实有缺失：按 `source-notes.md` 恢复并重新去 AI 味。

## 视觉要求

- 封面必生成 `cover.png`，使用 `scripts/render_editorial_cover.py` 和 `templates/cover-magazine-v1.html` 的新杂志人物模板。
- 封面不要直接使用完整长标题；必须使用 `title-card.json` 中的短字段。人物图、裁切和版式由封面预设池自动选择，不要让生成任务单独挑人物图。
- 正文图必须进入判断阶段，但数量可以是 0、1 或 2 张。
- 正文图只走轻量路径：信息图、场景图、对比图、流程/结构图。
- 生成前在 job 目录写 `visual-meta.json`，只记录本次 prompt 意图；不做视觉审核，不写入长期防重历史。
- 图片失败不阻断主流程：封面失败可跳过封面参数，正文图失败删除 marker，最终报告说明“配图失败，已跳过”。
- 不做 OCR、识图、图片相似度、视觉评分等低性价比检查。

### 正文图注入避坑

`publish_pipe.py` 只有一个正文图注入入口：`image_injector.py`。写稿时不要同时在 Markdown 里写 `![...](body-1.png)` 又在发布命令里传 `--images body-1.png`，否则 HTML 可能出现重复图片并导致上传日志里同一张图上传两次。Cron 推荐做法：正文只放段落和图位意图，生成图片后通过 `--images /abs/job/body-1.png` 交给管线按位置注入；如果选择 Markdown 原生图片，就不要再把同一文件传给 `--images`。


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
source-notes.md
title-card.json
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
封面标题：
文章大意：
为什么选这个题：
来源数量：
事实底稿是否完成：
空话密度：
关键事实是否保留：
是否避开敏感题：
是否与近期大意重复：
去 AI 味是否完成：
封面/正文图结果：
dry-run/草稿箱结果：
产物路径：
```

这些字段只用于汇报执行结果，不是文章结构模板。

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
