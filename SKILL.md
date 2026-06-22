---
name: xiaohu-wechat-publishing
description: |
  Use when working with WeChat Official Account: topic planning, writing, formatting, cover/body visuals, and draft-box publishing. Triggers: 写公众号, 微信排版, 公众号文章, 推草稿箱, 发公众号, 熵增时刻, 思想的野路子丶, or packaging an article for WeChat.
version: 4.7.0
author: Hermes curator
license: MIT
metadata:
  hermes:
    tags: [wechat, mp, article, pipeline, formatting, cover, publish, xiaohu]
---

# 小虎公众号生产与发布总管线

这是唯一主 skill。处理公众号任务时，只加载 `xiaohu-wechat-publishing`；写作、排版、封面、正文图、发布都在这里调度。

## 默认原则

- 默认走最短主路径：确认输入 → 必要写作/结构化 → 必要配图 → 排版 → 硬校验 → 发布。
- 用户只要排版，就不要进入发布链路；用户只要封面，就不要顺手改正文。
- 发布脚本只投递已验证产物，不临时猜封面、不修正文案、不绕过校验。
- 凭据只从 `~/.hermes/.env` 读取；不要把真实 app_id/app_secret 写进 skill。
- 正式产物默认写入 `~/.hermes/workspaces/wechat`。
- 正文、封面、图片里都不要写任何 AI 身份披露；`publish_pipe.py` 会硬扫描，命中直接失败。
- **创作质量与风险规避是最高优先级**：避开微信"低创作度"标签与政治财经高风险限流，规则见 `prompts/quality-and-risk.md`，与其他写作文件冲突时一律以它为准。

## 先读什么

按任务读最少的文件，别全量加载：

- **写任何正文前必读 `prompts/quality-and-risk.md`**（信息增量硬标准 + 去标题党 + 风险软规避 + 去同质化）。
- 写正文前读 `prompts/writing-persona.md` 和 `prompts/markdown-elements.md`。
- AI / 科技 / 产业稿额外读 `references/ai-tech-writing-guide.md`。
- 做封面或正文图前读 `prompts/visual-design.md`。
- 需要 Swiss Minimal 封面参数时读 `references/swiss-cover-usage.md`。
- 排查字体方框字读 `references/image-font-tofu-debug-2026-05.md`。
- 查完整历史规则或旧流程时才读 `references/legacy-skill-full-2026-05.md`。
- 查端到端实测命令时读 `references/e2e-pipeline-commands-2026-05.md`。
- 正文图注入场景和参数用法读 `references/body-image-injection-2026-05.md`。
- 正文图生成实操（baoyu 框架 + Agnes API 完整示例）读 `references/body-image-baoyu-agnes-workflow.md`。
- 人物素材库（可复用肖像图）读 `references/portrait-assets-library.md`。
- 发布参数配置（评论、作者、摘要）读 `references/publish-config-params-2026-05.md`。
- 早/晚定时任务的定稿提示词读 `references/cron-prompts-2026-06.md`。

## 运行方式

优先用统一入口，避免 Linux 多 Python 环境跑错解释器：

```bash
python3 scripts/run.py doctor.py --mode format
python3 scripts/run.py doctor.py --mode publish
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong --dry-run
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
```

`scripts/run.py` 会调用 `runtime.python_bin()`，自动选择安装了 `markdown`、`requests`、`PIL`、`playwright` 的 Python。

## 任务路由

1. 写作：用户给主题、标题、素材、口播或要求双账号成稿。
2. 排版：用户说“排版这篇”“微信排版”“format 一下”。
3. 配图：用户要封面、正文图、图位或视觉统一。
4. 发布：用户说“推草稿箱”“发公众号”“直接发”。

一句话包含多项时，默认顺序：写作 → 配图 → 排版 → 发布。用户明确说“不改文案 / 原文直接发”时，只做封面、排版和发布。

## 写作快路径

- **每篇必须满足信息增量硬标准（详见 `prompts/quality-and-risk.md`）**：≥3 个独立信息源、严禁单源洗稿（单源 >70% 重写）、含 ≥2 种原创分析（横向/纵向对比、数据测算、对普通人的可操作结论）。终稿自检一句："这篇给了读者哪条别处看不到的信息或判断？"答不出不发。
- **风险软规避**：不评判/预测政策走向、不预测股汇币涨跌、不喊点位、不荐买卖、不碰敏感时政/地缘/群体事件；财经科技只从"对普通人工作/消费/生活的影响"切入。
- **去标题党**：标题信息型/价值型，准确反映正文；禁止震惊体空转、夸张承诺。
- **去同质化**：双账号同日选题在事件/主题层面必须不同；发布前比对 publish-history，核心实体+结构高度相似则换题。
- **先搞清楚用户要的是什么类型的帖子，不要猜。** 当用户说的主题有歧义时（比如"互关帖"可能是分析互关利弊的文章，也可能是互关涨粉的 CTA 帖子），必须先确认意图再动笔。错误理解 = 白写 + 白排版 + 白发布 + 草稿箱多一篇废稿。用 clarify 或直接问一句再写。
- 起稿前用工具确认真实当前日期；新闻、政策、融资、公司动态、人物事件必须核查时间新鲜度。
- 标题和封面文案抛出问题，不把结论写死。
- **标题风格要按场景选，不要默认悬念型。** 可在信息直给型、问题讨论型、观点判断型、影响切口型、反差式、场景代入型、解释型之间选择，但无论选哪种，标题第一眼都必须让读者看懂“在讲什么事 / 什么对象”。
- **标题主体必须明确。** 至少保留 1 个具体主体词：公司、产品、平台、行业、场景、品类之一。不能只剩抽象钩子（如“谁在买单 / 谁在补差价 / 还是证据吗”）。主体不明确的标题直接重写。
- 双账号默认差异：
  - `xiaocong` / 熵增时刻：产业结构、科技逻辑、信息密度。
  - `yeluzi` / 思想的野路子丶：资本牌桌、冲突感、情绪推进。
- 2000-4000 字正文应至少使用 3 种非段落元素；表格、引用、列表、代码块等规则见 `prompts/markdown-elements.md`。
- 写完整篇后自检：如果全是纯段落，没有表格 / 列表 / 引用 / 代码块，直接重写结构。

## 配图快路径

**⚠️ 图位标记硬规则**：Markdown 里写了 `<!-- img:xxx -->` 就必须生成对应图片。如果不确定是否配图，**先不加标记**，排版完成后再决定是否插图。Dry-run 会拦截未解析的标记，但事后补图比一开始就不加更浪费。

封面默认用 Swiss Minimal，适合现成稿和快速发布：

```bash
python3 scripts/run.py render_cover_swiss.py \
  --brand '熵增时刻 · ENTROPY' \
  --title-line1 '你为什么' \
  --title-hl '总焦虑？' \
  --subtitle '不是脆弱，是不甘平庸的信号' \
  --issue 'VOL.05 / 2026' \
  --topic '成长 · 内耗 · 野心' \
  --out cover.png
```

需要完整商业编辑风封面时，用 `render_editorial_cover.py`。

**正文图默认风格：baoyu-comic 知识漫画**。用户认为扁平化信息图（flat infographic）"廉价"，正文图首选知识漫画风格（manga + dramatic/neutral tone），用画面叙事，不用文字说教。

- **共用配图规则**：双账号文章共用同一套配图，按小聪调性生成（dramatic/neutral，冷静解释型），yeluzi 不单独生成配图。
- **宝玉框架提示词**：加载 `baoyu-comic` skill，用 ZONES / LABELS / COLORS / STYLE / ASPECT 结构组织提示词。
- **LABELS 取舍**：结构化标签里只保留 1-2 个核心中文主题词（如"百亿补贴"）作为画面元素，其余数据、术语用英文关键词或视觉符号（箭头、图表、问号）代替，避免 Agnes 生成乱码中文。
- **中文字硬规则**：Agnes 模型对中文极不稳定。**提示词中最多出现一个主题词**，其余信息用画面元素、表情、构图表达。不要在提示词里要求多行中文说明、对话框、标签文字。如需文字信息，用 Python/PIL 后期叠加。
- **默认比例 1024x576（16:9 宽图）**，适合公众号正文嵌入。竖图场景用 576x1024。
- **Agnes API 调用规范**：
  - Base URL：`https://apihub.agnes-ai.com/v1/images/generations`（注意是 `apihub` 不是 `api`）
  - 模型固定：`agnes-image-2.0-flash`
  - 环境变量：`AGNES_API_KEY`
  - 超时 420 秒；返回 URL 用 `curl -sSL --max-time 60` 下载
  - 下载失败重试一次

## 排版快路径

已有 Markdown：

```bash
python3 scripts/run.py format.py --input article.md --theme newspaper --no-open
```

需要主题画廊时才用：

```bash
python3 scripts/run.py format.py --input article.md --gallery --recommend newspaper magazine ink
```

排版输出的正式发布文件是 `article.html`，不是 `preview.html`。

## 发布快路径

先 dry-run：

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --account xiaocong \
  --dry-run
```

dry-run 硬校验通过后再正式推送：

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --account xiaocong
```

双账号：

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --account xiaocong,yeluzi
```

## 发布前硬校验

`publish_pipe.py --dry-run` 和正式发布都会检查：

- `article.html` 存在。
- H1 / `--title` 是正式标题，不是账号名。
- 没有残留 `<!-- img:... -->` marker。
- 图位注入没有 missing。
- 封面存在。
- HTML 中本地图片文件存在。
- 正式发布时账号存在且 app_id / app_secret 齐全。
- `--input` 模式下 Markdown 不含 AI 身份披露黑名单。
- **高风险关键词软扫描**（warning 级，不阻断）：命中政策/市场预测/敏感时政等词会列出提醒，确认是否需改切口，详见 `prompts/quality-and-risk.md` C 节。

任何一项失败都不要发布。

## 目录与产物

默认工作区：

```text
~/.hermes/workspaces/wechat/
  jobs/
  cache/tokens/
  manual-format/
  publish-history.jsonl      # 机器自动归档（publish_pipe.py 写入，勿手编）
  publish-history.md         # cron 读写：选题去重 + 当日记录（见下方维护规则）
```

## publish-history.md 维护规则

`publish-history.md` 是定时任务用来选题去重和记录当日主题的文件。结构是 `## YYYY-MM-DD` 日期段，内含 `### 早间` / `### 晚间` 子段。

**⚠️ 追加位置硬规则**：新日期段永远追加到文件**末尾**，不要插在中间。插入中间会把前一天日期段的早间/晚间隔开，破坏文档结构。

- **早间 cron**：在文件末尾追加新 `## YYYY-MM-DD` 段 + `### 早间` 子段。
- **晚间 cron**：在当天已有的 `## YYYY-MM-DD` 段内追加 `### 晚间` 子段（当天早间 cron 已创建该段）。
- **追加方法**：patch 时 `old_string` 要匹配文件**最后一行内容**，不要匹配 `### 晚间` 这类在文件中多次出现的文本——会命中错误位置。

受管工作区入口仍可用：

```bash
python3 scripts/run.py wechat_pipeline.py build --input article.md --account xiaocong --cover cover.png --images hero.png
python3 scripts/run.py wechat_pipeline.py validate --dir ~/.hermes/workspaces/wechat/jobs/<job>/<account> --cover cover.png
python3 scripts/run.py wechat_pipeline.py publish --dir ~/.hermes/workspaces/wechat/jobs/<job>/<account> --cover cover.png --account xiaocong
```

## 常用脚本

- `scripts/run.py`：统一 Python 运行入口。
- `scripts/doctor.py`：环境检查；`--mode format` 不要求公众号凭据，`--mode publish` 要求凭据。
- `scripts/format.py`：Markdown → 微信兼容 HTML。
- `scripts/image_injector.py`：图位注入唯一来源。
- `scripts/publish_pipe.py`：排版 → 图位注入 → 硬校验 → 草稿箱发布主入口。
- `scripts/publish_history.py`：发布历史和 AI 披露扫描。
- `scripts/render_cover_swiss.py`：快速 Swiss Minimal 封面。
- `scripts/render_editorial_cover.py` / `scripts/render_editorial_body_modular.py`：商业编辑风封面和正文图。

## 失败处理

1. 环境问题：先跑 `python3 scripts/run.py doctor.py --mode format`；发布问题跑 `--mode publish`。
2. 图片缺失：检查 Markdown 图位、`--images`、`article.html`、`images/`。
3. 标题错误：检查 Markdown 第一个 `#` 和 `--title`。
4. 字体方框：读 `references/image-font-tofu-debug-2026-05.md`。
5. 旧流程或历史细节：读 `references/legacy-skill-full-2026-05.md`。

## 定时任务故障排查

**"status: ok" 不等于执行成功。** Cron 任务可能模型在跑、输出文件在写，但全程没有调用任何实际工具（写作脚本、发布脚本一个都没跑）。排查步骤：

1. **看产物是否存在**：检查 `~/.hermes/workspaces/wechat/jobs/<当天日期-am|evening>/` 目录是否创建、里面有没有 `xiaocong/` 和 `yeluzi/` 子目录、`article.md` / `cover.png` / `article.html` 是否存在。
2. **看发布历史是否更新**：读 `~/.hermes/workspaces/wechat/publish-history.jsonl` 最后几行，确认当天有没有记录。
3. **看 agent.log 执行轨迹**：`grep "cron_<job_id>" ~/.hermes/logs/agent.log`，关注：
   - 是否有 `tool terminal completed` 且执行的是 `publish_pipe.py` / `format.py` / `run.py` 等脚本
   - 是否全是 `web_search` + 思考，没有任何脚本调用
   - 是否出现 `Stream stale` / `Failed to rebuild shared OpenAI client` 错误
   - `Turn ended` 行的 `tool_turns` 数量：只有搜索没有发布 = 没跑发布流程
4. **看输出文件内容**：`~/.hermes/cron/output/<job_id>/` 下的 `.md` 文件包含完整 prompt + 最终回复。如果回复里有"草稿箱推送成功"但前面步骤 1/2 检查都失败，说明 agent 产生了幻觉——模型只写了报告没有实际执行。

详细调查记录见 `references/cron-execution-debug-2026-06.md`。

## 文档交付偏好（用户明确修正）

当用户要求“整理规则 / 做成文档 / 供转发给别的 Agent 审核”时，按下面方式交付：

- **直接产出可转发 Markdown 文档**，不要只在聊天里临时总结。
- **优先写入实体 `.md` 文件**，并在回复里明确给出绝对路径，方便用户转发或作为附件发送。
- **文档内容要自解释**：默认把本地脚本名、工具名、文件名翻译成“这是做什么的 / 它负责什么操作 / 它受什么规则约束”，不要假设外部读者认识当前仓库结构。
- **区分规则层级**：明确标出哪些是通用 skill 规则，哪些是定时任务/cron 追加的任务规则，避免把两者混成一层。
- **少废话、少过程描述**：用户此类需求要的是“可直接转发的成品”，不是你边解释边补充。
- 如果用户后续还问“文档路径在哪 / 能不能直接发”，说明上一次交付不完整；下次默认同时给出文档路径。

## 对外审阅文档输出规则

当用户要你“把规则整理出来”“发给别的 Agent 审核”“生成可转发文档”时，默认产物应是**可直接转发的独立 Markdown 文档**，而不是聊天式说明。

要求：
- 先按主题分类整理：抓热点规则、写文章规则、配图规则、排版规则、发布/校验规则、定时任务专属规则。
- 优先写“这个模块是干什么的、有什么规则、什么情况下触发、通过/失败条件是什么”，不要堆本地脚本名或路径。
- 如果必须提到脚本/文件，只能作为补充，主体必须用自然语言解释其作用，让外部 Agent 不依赖当前机器环境也能理解。
- 输出应可脱离当前对话独立阅读：少用“上面提到”“我刚查了”这类上下文依赖句。
- 风格要求：少废话、直接给成品；可以详细，但不要聊天腔解释。
- 若用户明确说“不要分析，只整理规则”，则禁止混入原因分析、优化建议、批评结论。

## 正文配图去重校验（新坑位）

当任务生成了 1-2 张正文图后，发布前除了检查 `<!-- img:... -->` marker 是否清空，还要额外检查最终 `article.html` 里**同一张正文图是否被重复插入两次**。

最常见的错误形态：
- 实际只生成了 2 张唯一图片；
- 但最终 HTML 里变成 4 个 `<img>`；
- 表现为每张正文图各出现两次（前文插一次，后文又插一次）。

校验要求：
- 检查最终 HTML 的正文 `<img>` 引用；
- 若唯一正文图文件数只有 1-2 个，但每个文件名重复出现两次，判定为**重复注入 bug**；
- 命中后不要发布，先排查注入链路是否发生了“正文已有插图 + 后置 section 再插一轮”的双重注入。

这条校验优先级高于“图片存在即可发布”；图片存在但重复注入，仍视为发布前失败。

## Output Contract

当用户要求“整理规则 / 做成文档 / 供转发给别的 Agent 审核”时，按下面方式交付：

- **直接产出可转发 Markdown 文档**，不要只在聊天里临时总结。
- **优先写入实体 `.md` 文件**，并在回复里明确给出绝对路径，方便用户转发或作为附件发送。
- **文档内容要自解释**：默认把本地脚本名、工具名、文件名翻译成“这是做什么的 / 它负责什么操作 / 它受什么规则约束”，不要假设外部读者认识当前仓库结构。
- **区分规则层级**：明确标出哪些是通用 skill 规则，哪些是定时任务/cron 追加的任务规则，避免把两者混成一层。
- **少废话、少过程描述**：用户此类需求要的是“可直接转发的成品”，不是你边解释边补充。
- 如果用户后续还问“文档路径在哪 / 能不能直接发”，说明上一次交付不完整；下次默认同时给出文档路径。

## Output Contract

默认先给可交付结果，再说明停在哪一步。失败时先讲失败原因，再给下一步。公众号任务优先保证“可发”，再优化细节。
