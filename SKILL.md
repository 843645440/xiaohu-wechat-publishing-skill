---
name: xiaohu-wechat-publishing
description: |
  Use when working with WeChat Official Account: topic planning, writing, formatting, cover/body visuals, and draft-box publishing. Triggers: 写公众号, 微信排版, 公众号文章, 推草稿箱, 发公众号, 熵增时刻, 思想的野路子丶, or packaging an article for WeChat.
version: 4.9.0
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
- 做封面或正文图前读 `references/baoyu-style-index.md`（三大 baoyu skill 风格索引 + 自动匹配规则）。
- 需要 Swiss Minimal 封面参数时读 `references/swiss-cover-usage.md`。
- 排查字体方框字读 `references/image-font-tofu-debug-2026-05.md`。
- 查完整历史规则或旧流程时：历史参考文件已清理，以 SKILL.md 和 `prompts/quality-and-risk.md` 为准。
- 查端到端实测命令时读 `references/e2e-pipeline-commands-2026-05.md`。
- 正文图注入场景和参数用法读 `references/body-image-injection-2026-05.md`。
- 正文图生成实操（baoyu 框架 + Agnes API 完整示例）读 `references/body-image-baoyu-agnes-workflow.md`。
- 人物素材库（可复用肖像图）读 `references/portrait-assets-library.md`。
- 发布参数配置（评论、作者、摘要）读 `references/publish-config-params-2026-05.md`。
- 早/晚定时任务的提示词直接在 `~/.hermes/cron/jobs.json` 里（v3.0），如需修改用 `execute_code` 或 cronjob 管理工具操作，不要在本 skill 目录里建参考副本。

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

一句话包含多项时，默认顺序：写作 → 配图 → 排版 → **发布前停步确认**。

## 入口与停步（灵活性硬规则）

不同使用强度对应不同停步点。**除非用户明确说“发/推草稿箱/直接发/发布”，否则 agent 完成被要求的步骤后必须停下，展示产物路径，问是否进入下一步。**

| 用户场景 | 典型说法 | agent 行为 | 代码命令 |
|---|---|---|---|
| 只排版 | “排版这篇”/“format 一下”/“微信排版” | 排版+注入+本地校验，**停在产物** | `publish_pipe.py --input X.md --cover C.png --dry-run` |
| 排版+配图但不发 | “做完整版给我看”/“排版配图” | 同上，**停在产物，明确告知“未发布”** | 同上 `--dry-run` |
| 全流程发布 | “推草稿箱”/“发公众号”/“直接发” | dry-run 通过后正式推 | dry-run → 去掉 `--dry-run` |
| 跳过排版发已有稿 | “这篇排好了直接发” | 信任已有 HTML | `publish_pipe.py --dir <目录> --cover C.png --account X` |
| 只写作 | 用户只给主题/素材 | 写完停下，**问“只排版还是发？”**，不自动继续 | 写作 + 等确认 |

### 三条停步硬原则

1. **默认停步**：用户没说出“发/推草稿箱/直接发/发布”等明确动词时，agent 完成被要求的步骤后**必须停下**，展示产物路径，问“要不要进入下一步”。
2. **dry-run 不是发布**：`--dry-run` 的产物**不能视为已发布**。用 `--dry-run` 完成排版后，必须明确报告“已排版/已配图，**未发布**”，严禁说“发布成功”。
3. **多步请求按序停步**：用户说“写完排版配图”，agent 做完这三步后停在发布前，即使没说“先停”。

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
  - `xiaocong` / 熵增时刻：科技、产业、AI、公司变化、行业变化。信息密度高、克制、有产业链视角、有数据和对比、少情绪多判断，像一个懂产业的朋友在解释复杂变化。优先结构：反常识开头 → 事件事实 → 产业链拆解 → 公司或技术路线对比 → 中国变量 → 普通人影响 → 克制结论。
  - `yeluzi` / 思想的野路子丶：民生、消费、职场、平台规则、普通人生活。更生活化、更有场景感，但不煽情、不站队、不制造对立，要有普通人的切身感。优先结构：普通人能感受到的变化 → 事件事实 → 谁受影响 → 规则或平台逻辑 → 中国规则补位或建设性变量 → 普通人怎么应对 → 克制结论。
- 2000-4000 字正文应至少使用 3 种非段落元素；表格、引用、列表、代码块等规则见 `prompts/markdown-elements.md`。
- 写完整篇后自检：如果全是纯段落，没有表格 / 列表 / 引用 / 代码块，直接重写结构。

## 配图快路径

**⚠️ 图位标记硬规则**：Markdown 里写了 `<!-- img:xxx -->` 就必须生成对应图片。如果不确定是否配图，**先不加标记**，排版完成后再决定是否插图。Dry-run 会拦截未解析的标记，但事后补图比一开始就不加更浪费。

**⚠️ 正文图相似性问题（待解决）**：用户反馈最近几天的正文图"看起来都是同一张"。md5 校验显示文件确实不同，但视觉上可能高度相似。可能原因：
- 提示词太泛化（如"科技、数据、连接"），导致 Agnes 生成风格雷同
- 需要在 cron prompt 里强制要求每篇文章的正文图提示词必须基于文章具体主题

如果用户再次反馈此问题，优先检查：
1. cron 执行时是否真的调用了 Agnes API（看 agent.log 里的 curl 命令）
2. 每次生成的提示词是否足够具体、差异化
3. 是否需要在 cron prompt（`~/.hermes/cron/jobs.json`）里加更严格的提示词要求

**⚠️ 配图容错原则（用户明确要求，2026-07-03）**：封面或正文图生成失败（API 超时、网络错误、返回空等）时，**不要中断发布流程**。
- 封面失败：跳过封面生成，发布时不传 --cover 参数（微信后台会要求手动补封面）。
- 正文图失败：移除 article.md 中对应的 <!-- img:xxx --> 标记，发布时不传 --images 参数。
- 最终报告中标注"配图失败，已跳过"。
- 原因：2026-07-03 晚间任务因 body_02.png 下载失败导致整个发布流程中断，用户明确要求配图失败就跳过。

封面默认用 Swiss Minimal，适合现成稿和快速发布：

```bash
python3 scripts/run.py render_cover_swiss.py \
  --brand '熵增时刻 · ENTROPY' \
  --title-line1 '你为什么' \
  --title-hl '总焦虑？' \
  --subtitle '不是脆弱，是不甘平庸的信号' \
  --issue 'VOL.05 / 2026' \
  --topic '成长 · 内耗 · 野心' \
  --out /absolute/path/to/cover.png
```

**⚠️ `--out` 必须用绝对路径。** 当从 job 目录（如 `~/.hermes/workspaces/wechat/jobs/2026-06-23-evening/yeluzi/`）运行时，相对路径 `--out cover.png` 会导致 Playwright 报 `net::ERR_INVALID_URL at file://cover.html/`。始终传入完整绝对路径。

需要完整商业编辑风封面时，用 `render_editorial_cover.py`。

**正文图风格自动匹配**：根据文章内容从三大 baoyu skill（article-illustrator / comic / infographic）中自动选择最合适的风格组合。详见 `references/baoyu-style-index.md`。

- **匹配流程**：分析文章内容信号 → 查 `baoyu-style-index.md` 的"内容类型 → 风格匹配表" → 选择推荐 Skill + Type/Layout + Style/Preset → 加载对应 baoyu skill 构造提示词。
- **生成模型**：统一使用 **Agnes Image 2.1 Flash**（`agnes-image-2.1-flash`）。
- **独立配图规则**：双账号各自生成各自的配图，根据文章内容自动选择合适风格。
- **中文字硬规则**：Agnes 模型对中文极不稳定。**提示词中最多出现 1-2 个中文主题词**，其余信息用英文关键词、画面元素、表情、构图表达。不要在提示词里要求多行中文说明、对话框、标签文字。如需精确中文文字，用 Python/PIL 后期叠加。
- **默认比例 1024x576（16:9 宽图）**，适合公众号正文嵌入。竖图场景用 576x1024。
- **Agnes API 调用规范**：
  - Base URL：`https://apihub.agnes-ai.com/v1/images/generations`（注意是 `apihub` 不是 `api`）
  - 模型固定：`agnes-image-2.1-flash`
  - 环境变量：`AGNES_API_KEY`
  - 超时 420 秒；返回 URL 用 `curl -sSL --max-time 60` 下载
  - 下载失败重试一次
  - **⚠️ 代理绕过**：系统环境设置了 `https_proxy=http://127.0.0.1:7890`，会导致 Agnes API 的 SSL 握手失败（`SSL_ERROR_SYSCALL`）。所有 curl 调用 Agnes API 时必须加 `--noproxy '*'`，包括生成请求和图片下载。示例：
    ```bash
    curl -sSL --max-time 420 --noproxy '*' \
      -X POST "https://apihub.agnes-ai.com/v1/images/generations" \
      -H "Authorization: Bearer $AGNES_KEY" ...
    ```

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

**⚠️ `format.py --output` 输出结构陷阱**：当使用 `--output /path/to/article.html` 时，format.py 不会创建一个名为 `article.html` 的文件，而是创建一个**目录** `article.html/`，内部结构为 `article.html/article/article.html` + `article.html/preview.html`。这会导致后续 `publish_pipe.py --dir` 失败（报 `IsADirectoryError`）。

**正确做法**：
1. **推荐**：不传 `--output`，让 format.py 输出到默认的 `format/article/` 子目录，然后手动复制：
   ```bash
   python3 scripts/run.py format.py --input /job/dir/article.md --theme newspaper
   # 输出在 /job/dir/format/article/article.html
   cp /job/dir/format/article/article.html /job/dir/article.html
   rm -rf /job/dir/format
   ```
2. **或者**：传 `--output` 为一个目录名（不是文件名），然后手动提取：
   ```bash
   python3 scripts/run.py format.py --input article.md --output /job/dir/formatted --theme newspaper
   # 输出在 /job/dir/formatted/article/article.html
   mv /job/dir/formatted/article/article.html /job/dir/article.html
   rm -rf /job/dir/formatted
   ```
3. **最简路径**：直接用 `publish_pipe.py --input article.md --job-dir /job/dir`，它会自动处理排版+发布，无需手动处理 format.py 输出结构。

## 发布快路径

**评论设置**：默认开启"所有人可评论"（`only_fans_can_comment: 0`）。如需改回"仅关注者可评论"，需修改 `scripts/publish_pipe.py` 中的 `push_draft()` 函数。

### `--input --job-dir` 模式（cron 任务推荐用这个）

**这是 cron 任务的最简路径。** 一条命令完成排版 + 图位注入 + 发布，无需手动复制文件。

```bash
# dry-run 校验
python3 scripts/run.py publish_pipe.py \
  --input /abs/path/to/job/article.md \
  --cover /abs/path/to/job/cover.png \
  --job-dir /abs/path/to/job \
  --account yeluzi \
  --dry-run

# 正式发布
python3 scripts/run.py publish_pipe.py \
  --input /abs/path/to/job/article.md \
  --cover /abs/path/to/job/cover.png \
  --job-dir /abs/path/to/job \
  --account yeluzi
```

排版输出自动写入 `<job-dir>/format/article/`，图片注入和发布都自动处理。

**⚠️ `--cover` 和 `--images` 必须用绝对路径。** 相对路径会被解析为相对于当前工作目录，而不是 job 目录。

### `--dir` 模式（已有排版 HTML 时用）

`--dir` 模式要求 job 目录里已经有 `article.html`（在目录根层级，不是 `article/article.html` 子目录）。适用于跳过排版、直接发布已有 HTML 的场景。

```bash
python3 scripts/run.py publish_pipe.py \
  --dir /abs/path/to/job \
  --cover /abs/path/to/job/cover.png \
  --account yeluzi
```

**⚠️ `--dir` 模式下 `--cover` 必须用绝对路径。** 相对路径会被解析为相对于 skill 目录（`~/.hermes/skills/wechat/xiaohu-wechat-publishing/`），而不是 job 目录。

**⚠️ `article.html` 位置陷阱**：`format.py` 输出到 `<job-dir>/article/article.html`（子目录内），但 `--dir` 模式要求 `<job-dir>/article.html`（根层级）。如果 cron 任务指示用 `--dir` 模式，必须先跑 format.py 再手动复制：
```bash
# format.py 输出到子目录
python3 scripts/run.py format.py --input /job-dir/article.md --output /job-dir --theme newspaper --no-open
# 复制到根层级
cp /job-dir/article/article.html /job-dir/article.html
# 然后再跑 --dir 模式
python3 scripts/run.py publish_pipe.py --dir /job-dir --cover /job-dir/cover.png --account yeluzi
```
或者直接用 `--input --job-dir` 模式跳过这个步骤（见上方"排版快路径"的最简路径）。

### `--input` 模式（手动排版用）

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

**⚠️ `--images` 多图片必须空格分隔**（argparse `nargs='*'`），**不要用逗号**：

```bash
# 正确
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --images body_01.png body_02.png \
  --account yeluzi

# 错误（逗号分隔会被当成一个路径，导致全部图片找不到）
--images body_01.png,body_02.png
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
- `--input` 模式下 Markdown 不含 AI 身份披露黑名单。**此扫描为发布前硬门禁，不可关闭**（`--skip-ai-guard` 已移除）。
- **高风险关键词软扫描**（warning 级，不阻断）：命中政策/市场预测/敏感时政等词会列出提醒（词表见 `data/high-risk-keywords.json`，含"大盘"等易误报词提示），确认是否需改切口，详见 `prompts/quality-and-risk.md` C 节。

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
5. 旧流程或历史细节：已归档清理，以 SKILL.md 为准。

## 定时任务故障排查

**Skill 加载失败 "skill(s) not found" — 顶层目录问题（2026-07-02 确认）**：Cron 调度器只在 `~/.hermes/skills/<name>/SKILL.md` 顶层查找 skill，**不会递归搜索子目录**。如果 skill 只存在于 `~/.hermes/skills/wechat/xiaohu-wechat-publishing/`，cron 会报：

> ⚠️ Skill(s) not found and skipped: xiaohu-wechat-publishing

任务会"执行"但 agent 没拿到 skill 指令，只会看到原始 prompt，产出垃圾（如反问用户"文章内容是什么"而不是写作发布）。

**修复**：确保顶层软链接存在：
```bash
ln -s ~/.hermes/skills/wechat/xiaohu-wechat-publishing ~/.hermes/skills/xiaohu-wechat-publishing
```

**检测**：如果 cron 输出显示 "Skill(s) not found" 警告，检查 `~/.hermes/cron/output/<job_id>/` 最新日志。早间（7:00, xiaocong）和晚间（17:00, yeluzi）任务都依赖此 skill 可加载。

**Skill 名称歧义（name 字段冲突）**：存在多个 SKILL.md 文件都含 `name: xiaohu-wechat-publishing`（如 `archived/xiaohu-wechat-publishing-v1/`、`wechat/xiaohu-wechat-publishing.backup-*/`），cron 调度器发现多个同名 skill 时**直接跳过加载**，输出 `[SILENT]`，不报错。`skill_view()` 也会拒绝猜测。

**修复**（2026-07-02 确认）：
1. 删除或重命名旧副本的 `name:` 字段：
   ```bash
   sed -i 's/^name: xiaohu-wechat-publishing$/name: xiaohu-wechat-publishing-v1/' \
     ~/.hermes/skills/archived/xiaohu-wechat-publishing-v1/SKILL.md
   ```
2. 或直接删除旧副本目录：`rm -rf ~/.hermes/skills/archived/xiaohu-wechat-publishing-v1/`
3. 确认只剩一个文件含 `name: xiaohu-wechat-publishing`：
   ```bash
   grep -rl "^name: xiaohu-wechat-publishing$" ~/.hermes/skills/
   ```

**软链接不是万能修复**：即使创建了顶层软链接 `~/.hermes/skills/xiaohu-wechat-publishing → wechat/xiaohu-wechat-publishing/`，如果 archived/backup 目录里还有同名 `name:` 字段，cron 仍会因歧义跳过。**必须同时消除名称冲突。**

**"status: ok" 不等于执行成功。** Cron 任务可能模型在跑、输出文件在写，但全程没有调用任何实际工具（写作脚本、发布脚本一个都没跑）。排查步骤：

1. **看产物是否存在**：检查 `~/.hermes/workspaces/wechat/jobs/<当天日期-am|evening>/` 目录是否创建、里面有没有 `xiaocong/` 和 `yeluzi/` 子目录、`article.md` / `cover.png` / `article.html` 是否存在。
2. **看发布历史是否更新**：读 `~/.hermes/workspaces/wechat/publish-history.jsonl` 最后几行，确认当天有没有记录。
3. **看 agent.log 执行轨迹**：`grep "cron_<job_id>" ~/.hermes/logs/agent.log`，关注：
   - 是否有 `tool terminal completed` 且执行的是 `publish_pipe.py` / `format.py` / `run.py` 等脚本
   - 是否全是 `web_search` + 思考，没有任何脚本调用
   - 是否出现 `Stream stale` / `Failed to rebuild shared OpenAI client` 错误
   - `Turn ended` 行的 `tool_turns` 数量：只有搜索没有发布 = 没跑发布流程
4. **看输出文件内容**：`~/.hermes/cron/output/<job_id>/` 下的 `.md` 文件包含完整 prompt + 最终回复。如果回复里有"草稿箱推送成功"但前面步骤 1/2 检查都失败，说明 agent 产生了幻觉——模型只写了报告没有实际执行。
5. **模型提前停止并编造原因（2026-07-03 确认）**：agent 完成部分工作（如 article.md + cover.png + 1张正文图）后停止，输出声称"工具调用被拒绝"，但日志显示 `finish_reason=stop`（模型主动停止，非被拒绝）。排查时**不要信任 agent 的自我解释**，必须对照 agent.log 验证：
   - 如果日志显示 `Turn ended: reason=text_response(finish_reason=stop)` 且 `api_calls` 远小于 budget（如 18/60），说明模型提前决定停止
   - 如果 agent 输出说"被拒绝"/"出错"但日志没有对应 ERROR/WARNING，说明是幻觉
   - 此时需要手动补完任务：检查产物目录缺什么，手动下载缺失图片，手动跑 `publish_pipe.py`

详细调查记录见 `references/cron-execution-debug-2026-06.md`。

## Cron prompt ↔ Skill 同步

Cron prompt（`~/.hermes/cron/jobs.json`）和本 skill 必须保持一致。升级 prompt 时按以下 4 点检查 skill 侧：

1. **账号人设三处一致**：SKILL.md 双账号差异段 + AGENTS.md "Two accounts" 段 + prompt 定位描述。
2. **AI 标识措辞**：prompt 中"AI 辅助"只在报告层，文章正文硬门禁（`publish_pipe.py` AI 披露扫描）不可突破。
3. **无参考副本**：skill 目录不存 cron prompt 副本，`jobs.json` 是唯一真相源。
4. **发布命令模式**：prompt 中用 `--input --job-dir`（cron 最简路径），路径参数全绝对。

详细冲突记录和修复方式见 `references/cron-prompt-sync-2026-07.md`。

优先级：`prompts/quality-and-risk.md` > skill `SKILL.md` > cron 提示词。

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

## ⚠️ 用户自带截图/图片的文章发布（高优先级）

**⚠️ 硬规则：用户提供截图时，必须将图片实际嵌入文章，不要只用文字描述截图内容。** 这是用户明确纠正过的错误——写"首页有xxx按钮"而不放截图 = 白做。用户会直接问"截图呢？"。

**完整工作流程**：

1. **复制图片到文章目录**（从 `~/.hermes/image_cache/` 复制到文章工作目录，用序号命名）：
   ```bash
   cp ~/.hermes/image_cache/img_xxx.jpg /job/dir/01-homepage.jpg
   cp ~/.hermes/image_cache/img_yyy.jpg /job/dir/02-themes.jpg
   ```

2. **在 Markdown 中用 `<!-- img:xxx -->` 标记图位**，放在对应描述段落后面：
   ```markdown
   打开网站，首页很简洁...
   <!-- img:01-homepage.jpg -->
   
   点击"浏览风格"，可以看到所有排版风格...
   <!-- img:02-themes.jpg -->
   ```

3. **发布时通过 `--images` 传入所有图片的绝对路径**（空格分隔，不是逗号）：
   ```bash
   python3 scripts/run.py publish_pipe.py \
     --input /job/dir/article.md \
     --cover /job/dir/cover.png \
     --images /job/dir/01-homepage.jpg /job/dir/02-themes.jpg /job/dir/03-format.jpg \
     --account xiaocong
   ```

4. **自检清单**：发布前确认 (a) 每个 `<!-- img:xxx -->` 都有对应文件存在，(b) `--images` 参数包含了所有截图的绝对路径，(c) 文章里不是只用文字描述截图内容。

## 正文图注入架构（重要）

**图片注入只允许在发布阶段统一处理一次。** 排版阶段（`format.py`）不再处理 `<!-- img:... -->` 标记，而是保留原样交给 `publish_pipe.py`。

### 为什么这样设计
2026-06 发现一个重复注入 bug：
- `format.py` 先把 marker 转成 Markdown 图片 `![img](...)`
- `publish_pipe.py` 发现 HTML 里没有 marker 了，但命令行传了 `--images`
- 于是按位置再插一轮
- 结果：同一张图出现两次（正文插一次，section 再插一次）

### 修复方案（B 方案）
- `format.py` 的 `process_img_markers()` 现在直接返回原文，不转换 marker
- `publish_pipe.py` 在排版完成后统一调用 `image_injector.inject()` 处理所有图片
- 这样保证每张图片只注入一次

### 校验要求
发布前检查最终 `article.html`：
- 若唯一正文图文件数只有 1-2 个，但每个文件名重复出现两次，判定为**重复注入 bug**
- 命中后不要发布，先排查注入链路

### Dry-run 写回 bug（2026-06-25 修复）
`publish_pipe.py` 在图片注入后会写回 `article.html`。如果 dry-run 也写回，markers 就被替换成了 `<img>` 标签。后续正式发布时 `article.html` 里已无 markers，`image_injector.inject()` 会走 `inject_by_position()` 按位置再插一轮 → 每张图片出现两次。

**修复**：dry-run 模式下不写回 `article.html`（`if not args.dry_run:` 守卫）。

**诊断方法**：dry-run 后检查 `article.html` 是否仍包含 `<!-- img:xxx -->` 标记。如果没有了，说明写回发生了，正式发布会产生重复图。此时需要重新 `format.py` 生成干净的 `article.html` 再发布。

**操作规则**：dry-run 和正式发布之间不要手动编辑 `article.html`。如果 dry-run 发现问题需要修，修完 Markdown 后重新走 format → copy → dry-run → publish 全流程。

## Output Contract

默认先给可交付结果，再说明停在哪一步。失败时先讲失败原因，再给下一步。公众号任务优先保证"可发"，再优化细节。
