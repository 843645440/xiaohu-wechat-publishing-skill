---
name: xiaohu-wechat-publishing
description: |
  公众号内容生产与发布单一主 skill：从选题、标题、正文、去 AI 味、信源核验、配图、封面、排版到草稿箱发布，统一在这里完成。

  触发场景：
  - 用户说"写公众号""公众号文章""微信排版""推草稿箱""发公众号"
  - 用户要求"熵增时刻 / 思想的野路子丶"账号的文章生产、封面、排版或发布
  - 用户给现成标题、正文或文章路径，希望一路处理到草稿箱
version: 3.9.0
author: Hermes curator
license: MIT
metadata:
  hermes:
    tags: [wechat, mp, article, pipeline, formatting, cover, publish, xiaohu]
requires_environment_variables:
  - WECHAT_APPID_XIAOCONG
  - WECHAT_SECRET_XIAOCONG
  - WECHAT_APPID_YELUZI
  - WECHAT_SECRET_YELUZI
---

# 小虎公众号发布总管线（最终单 skill 版）

这是公众号内容工作的**唯一主 skill**。

以后处理公众号任务时，默认只加载 `xiaohu-wechat-publishing`，不要再把任务拆去寻找多个公众号 skill。写作、改稿、核验、排版、封面、配图、发布，都以这里的规则、命令和约定为准。

## 新会话最小执行规则（最高优先级）

如果是新会话，或当前智能体不够强、上下文不完整，**不要先读完整份长文档再自己发明流程**，直接按下面这套最小规则执行。

### 0. 一条总原则
- **默认走最短主路径，不走兼容路径。**
- 只有用户明确说“兼容旧稿 / legacy / 复用旧模板”时，才允许调用旧入口。

### 1. 任务路由四分法
先判断用户现在要的是什么，只能四选一：

1. **写作**：写公众号、改写、双账号成稿
2. **配图**：只做封面 / 只做正文图 / 调视觉
3. **排版**：把 Markdown / 正文排成微信 HTML
4. **发布**：把已经准备好的文章推到草稿箱
5. **模块正文图**：为文章生成 1 张总量级冲击图 + 1 张人物-公司-市值卡 + 1 张结构影响图，默认使用 `scripts/render_editorial_body_modular.py`

如果用户一句话里同时包含多项，默认按：
**写作 → 配图 → 排版 → 发布**

### 2. 模式判断（去掉歧义版）
- 用户只给**主题 / 一句话方向**，且没说“直接全文” → **先给标题 + 大纲**
- 用户给**标题**，且没说“先看提纲” → **直接出正文初稿**
- 用户给**现成文章 / 链接 / Markdown 文件**并要求改写 → **直接进入改写成稿**
- 用户说“每一步我看”“先给我看一版”“逐步来” → **逐步确认模式**
- 用户说“直接写完”“直接出全文”“直接走完整流程” → **全自动模式**

### 3. 双账号任务默认规则
当用户说“发两个公众号 / 分两种风格 / 熵增和野路子都要”时：
- 默认必须产出**两篇完整版本**
- **熵增时刻**：产业 / 科技 / 结构 / 信息密度
- **野路子**：资本 / 博弈 / 情绪推进 / 冲突感
- 用户后续回“A / B”时，默认理解为**显示顺序或偏好**，不是砍掉另一篇

### 4. 写作风格优先级（硬规则）

**起稿前必须加载 `prompts/writing-persona.md`**——这是小黑财经风格的人格模板，包含节奏、冲突感、情绪推进规则和双账号差异化叠加。不加载就写，第一稿几乎一定风格偏差，导致返工。

发生风格冲突时，按这个优先级决策：
1. **用户当次明确要求**
2. **`prompts/writing-persona.md` 里的风格定义**
3. **本 skill 里的双账号默认规则**
4. **熵增 AI/科技题材时加载 `references/ai-tech-writing-guide.md`**
5. **历史兼容口径**

补充：
- 熵增写 AI / 科技 / 中美科技竞争 / 产业趋势时，必须额外加载 `references/ai-tech-writing-guide.md`
- 野路子默认不用加载这个 guide，除非用户明确要求按熵增那套科技深度写法处理
- **风格偏差是写作阶段最大的返工来源**——起稿前花 10 秒加载 persona 模板，比写完 2000 字再改风格高效得多

### 5. 视觉执行唯一主路径
新稿默认只允许使用以下正式入口：
- **封面正式入口**：`scripts/render_editorial_cover.py`
- **正文整页图正式入口**：`scripts/render_editorial_body.py`
- **正文模块图正式入口**：`scripts/render_editorial_body_modular.py`（hero/people/structure 三模板制，新稿正文图默认优先于此）
- **正文图注入**：`scripts/inject_body_images.py`（排版后自动插入正文图到 HTML）
- **视觉规范**：`references/business-editorial-visual-system-v1.md`

### 6. 发布前唯一硬检查
发布前必须做且只做这四项硬检查：
1. **检查目标账号**：使用 `--account xiaocong` 或 `--account yeluzi`（自动从 `~/.hermes/.env` 读取凭据）
2. **检查真实输出目录**：`--dir` 指向 format.py 的 `--output` 目录即可（脚本会自动下钻找到 `article.html`）
3. **检查正文图是否进 HTML**：`grep -c '<img' article.html`
4. **检查封面是否明确指定**：优先 `--cover images/cover.png`

补充硬约束：
- `publish.py` 若显式传入 `--cover` 但文件不存在，必须直接报错退出，严禁静默 fallback 到正文第一张图。
- 即使未传 `--cover`，也只允许在 `images/` 下查找 `cover*` 文件；若不存在，同样必须中止发布。
- 正式发布目录唯一推荐契约：`<article_dir>/images/cover.png`

### 7. 账号切换（已自动化）
**新方式（推荐）**：使用 `--account` 参数，一行命令搞定切换：
```bash
python3 publish.py --account xiaocong --dir /path --cover cover.png
python3 publish.py --account yeluzi --dir /path --cover cover.png
```
- 凭据自动从 `~/.hermes/.env` 的 `WECHAT_APPID_*/WECHAT_SECRET_*/WECHAT_AUTHOR_*` 读取
- 不再需要手动修改 `config.json`，不再需要手动清除 token 缓存
- ConfigGuard 仍然保护 config.json 不被意外修改

**旧方式（兼容）**：不带 `--account` 时，使用 config.json 里的默认凭据。

### 8. 正文图自动注入（含已知坑）
使用 `scripts/inject_body_images.py` 在排版后自动插入正文图：
```bash
# 方式1：指定图片文件（按 h2 标题顺序插入）
python3 inject_body_images.py --html article.html --images img1.png img2.png img3.png

# 方式2：指定图片目录（自动扫描，排除 cover*）
python3 inject_body_images.py --html article.html --images /path/to/images/

# 方式3（标记模式）：在 Markdown 中用标记指定插入位置
# 在 Markdown 里写：<!-- img:filename -->，注入脚本会自动替换
```

**已知坑（2026-05 实测）**：
- `--mode marker` 有时会 fallback 到文末追加，日志提示"没有足够的标题位置"
- `<!-- img:filename -->` 标记经过 format.py 后在 article.html 中的位置可能漂移
- **推荐**：排版完成后，直接在 article.html 中用 Python 定位目标文本，手动插入 `<section><img>` 标签（见上方"正文图注入的实际坑与解法"段落）

### 9. 如果智能体拿不准，只允许这样保守处理
- 写作任务：先给标题+大纲，不直接乱发全文
- 配图任务：只走 `render_editorial_cover.py` / `render_editorial_body.py`
- 发布任务：先检查账号和真实输出目录，再发
- 不要因为 skill 里有兼容脚本，就自动走兼容路径

## 当前重构后的执行原则（2026-05 新增）
- 封面：**轻量参数化**，少变量，强模板。
- 正文图：**模块化拼装**，按文章类型选模块，不做万能大模板。
- 排版：只做格式转换，不负责猜图位。
- 发布：只做最后投递，不负责修正文案。
- 兼容路径：仅保留最少必要兼容，不做默认入口。
- 新稿默认必须收敛到**一个主链路**，不再允许“写一点、补一点、猜一点”地拼流程。

## 用户协作与执行节奏（2026-05 新增）

### A. 不要空口承诺，必须边做边报进度
用户对“说要开始了，但实际上没继续跑”容忍度低。

强制规则：
- 当进入公众号自动化实操阶段时，不要只回答“开始做了”“我继续”这类口头承诺。
- 必须在同一轮里实际推进到可验证产物，例如：写出 Markdown、统计字数、生成图片、排版、发布、或输出错误定位结果。
- 每完成一个关键阶段，要明确汇报：**已完成什么 / 还差什么 / 为什么没进入下一步**。

### B. 长任务默认持续执行，除非用户明确叫停
用户偏好是：既然已经授权“都按你的来”，就持续推进直到形成可交付结果，不要频繁停在中间征求同意。

适用场景：
- 双账号写稿
- 配图与封面
- 排版
- 草稿箱测试发布
- 工作流重构与清理

### C. 口播转公众号时，先把正文做对，再进后链路
如果用户给的是视频口播稿并要求“写两篇公众号并测试发布”：
- 先快速产出双稿
- 立刻检查字数是否达到用户要求
- 若字数不足，先扩稿，不要急着进封面/正文图/发布
- 避免发布一个 900～1000 字的测试半成品，导致后面所有问题都掺杂“内容长度不合格”的噪音

## 最终交付型工作流（2026-05 新增）

目标：把公众号生产线收敛成一个长期可运行、少分支、低返工的交付流程。

### 主链路（唯一默认路径）
1. 输入素材
2. 提炼核心结论与双账号角度
3. 先定标题与正文结构
4. 并行写双稿
5. 生成模块化正文图（hero / people / structure / compare）
6. 生成轻量参数化封面
7. 将正文图嵌入对应段落
8. 把图片放入最终发布目录
9. 运行排版
10. 运行总控校验
11. 发布草稿箱

### 强制约束
- 不允许把正文图统一堆到文末
- 不允许把封面作为发布后补丁
- 不允许用兼容路径取代主路径
- 不允许跳过总控校验直接发布
- 不允许“先发再补救”作为默认策略

### 兼容路径策略
- 兼容脚本只用于旧稿修复或历史资料回放
- 新稿默认只走正式入口
- 若新稿还要调用兼容路径，必须视为流程缺陷而不是正常设计

### 终局判断
一条流程是否合格，只看四件事：
- 是否能稳定产出两篇稿
- 是否能稳定出图
- 是否能稳定排版
- 是否能稳定进草稿箱

只要其中任一项不稳定，就不算可交付工作流。

## Overview

这个 skill 把公众号工作拆成一条清晰的生产线：
- 你给**选题**，我一路做到草稿箱；
- 你给**标题**，我补齐正文、配图、封面、排版，直到草稿成功；
- 你给**现成文章**，我先分析，再改写，再排版，再发布；
- 你要**一步一步介入**，我就按阶段停下来等你确认。

目标不是堆流程，而是让公众号内容能稳定产出、稳定发出去。

## format.py 参数与行为备忘（2026-05 实测）
- `format.py` 参数是 `--input`（不是位置参数，也不是 `--dir`）
- `--output` 指定输出目录路径（如 `/home/ubuntu/tmp_xc.html`）
- `--format wechat` 指定微信格式
- 输出结构：`<output_dir>/<input_stem>/article.html` + `preview.html` + `images/`
- **preview.html 是壳模板**（只有 `{{content}}` 占位符），实际排版内容在 `article.html` 里
- **`<!-- img:filename -->` 标记已由 `process_img_markers()` 在排版时直接转为 `<img>` 标签**（2026-05 修复），位置精确对应 Markdown 中的标记位置，不再需要手动注入
- 排版输出的标题从 Markdown 第一个 `#` 行自动提取
- **运行脚本优先使用 `~/.hermes/hermes-agent/venv/bin/python3`**；系统 `python3` 可能缺少 `markdown` 等依赖，导致 `format.py` 直接失败

## 正文图注入说明（2026-05 更新）

**新管线（默认）**：`publish_pipe.py` + format.py 内置 `process_img_markers()` 自动处理 `<!-- img:filename -->` 标记，排版时图片直接到位，无需额外注入步骤。

**旧 inject 脚本（兼容）**：`scripts/inject_body_images.py` 保留可用，但不再作为默认入口。历史坑：marker 模式有时 fallback 到文末追加；需手动修改 HTML 纠正位置。新稿不要再用。

**图片路径规则**：
- Markdown 中写 `<!-- img:filename.png -->`
- 图片文件放在 Markdown 同目录或 config.json 的 `image_search_paths` 中
- format.py 自动复制到 `images/` 并转为 `<img>` 标签
- 发布时 publish_pipe.py 自动上传到微信 CDN

## 一键发布管线 publish_pipe.py（2026-05 新增，推荐默认入口）

**新管线** `scripts/publish_pipe.py` 把排版→图片注入→发布合并为一条命令，消除手动修补环节。

### 为什么需要它
旧流程需要 5 步：format.py → inject_body_images.py → 手动修 HTML → 清 token → publish.py
- `inject_body_images.py` 的 marker 模式不可靠，经常把图片追加到文末
- 中间需要手动修改 article.html 才能纠正图片位置
- 多个脚本串联，任何一步出错都要从头来

### 改进点
1. **format.py 内置 img 标记处理**：`<!-- img:filename -->` 在排版时直接转为 `![img](images/xxx)` → `<img>` 标签，位置精确
2. **publish_pipe.py 一键搞定**：`--input article.md --cover cover.png --images hero.png --account xiaocong`
3. **封面必填**：缺失直接失败，不再有静默 fallback
4. **无需单独清 token**：按 app_id 自动缓存隔离

### 用法
```bash
PY=~/.hermes/hermes-agent/venv/bin/python3
SCRIPTS=~/.hermes/skills/xiaohu-wechat-publishing/scripts

# 完整一键：Markdown → 草稿箱
$PY $SCRIPTS/publish_pipe.py \
  --input /home/ubuntu/tmp_xc.md \
  --cover /home/ubuntu/xc_cover.png \
  --images /home/ubuntu/xc_hero.png \
  --account xiaocong

# 仅排版+注入，不推送
$PY $SCRIPTS/publish_pipe.py \
  --input /home/ubuntu/tmp_xc.md \
  --cover /home/ubuntu/xc_cover.png \
  --images /home/ubuntu/xc_hero.png \
  --dry-run

# 跳过排版，发布已有 article.html
$PY $SCRIPTS/publish_pipe.py \
  --dir /home/ubuntu/tmp_xc.html/tmp_xc \
  --cover /home/ubuntu/xc_cover.png \
  --account yeluzi
```

### 写作人格模板
起稿前加载 `prompts/writing-persona.md`，里面定义了小黑财经风格的节奏、冲突感、情绪推进规则和双账号差异化叠加。避免第一稿风格偏差导致返工。

### 旧脚本兼容
- `publish.py` 仍然可用，不受影响
- `inject_body_images.py` 保留但不再推荐作为默认入口
- 新稿默认走 `publish_pipe.py`，旧稿修复或特殊场景可用旧脚本

## 关键支持文件
- `prompts/writing-persona.md`：小黑财经风格写作人格模板（起稿前必须加载，双账号统一风格基座+差异化叠加）
- `references/wechat-pipeline-rebuild-sop-2026-05.md`：本轮重构后的公众号稳定工作流设计输入，记录主链路、失败模式、模块化正文图策略与长期收敛方向。未来若继续工程化，优先参考它而不是临时会话结论。
- `references/e2e-pipeline-commands-2026-05.md`：端到端发布管线命令速查，包含封面/正文图/排版/注入/发布的完整命令序列、输出结构、已知坑和耗时参考。新会话执行发布时优先查阅此文件。
- `references/image-font-tofu-debug-2026-05.md`：封面/正文图中文显示为方框（tofu）时的字体排查与紧急修复记录；包含确认中文字体、Hermes venv + PIL 检查、绕开 Playwright 直接用 WQY Zen Hei 绘制 PNG、以及用户要求直接看图时停止重推草稿的纠正流程。

### 图片中文字方框（tofu）硬规则（2026-05 新增）

当用户反馈“封面图/正文图是框框”“图片没改变”“文字显示异常”时，优先按 `references/image-font-tofu-debug-2026-05.md` 处理：
1. **不要继续反复重推草稿**；先排查字体源和渲染路径。
2. 同时检查/重做**封面图和正文图**，不要只修正文图。
3. HTML/Playwright 截图可能因 Chromium 中文字体 fallback 失败产生方框；紧急交付时改用 PIL 并强制中文字体 `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`。
4. 如果用户要求“生成完直接发我，我来换”，直接返回 `MEDIA:/absolute/path.png` 图片文件，不再先发布/重推草稿。
5. 生成图片后优先让用户目测确认；不要把“本地视觉分析通过”当成微信后台实际显示通过。

## When to Use

使用本 skill 当用户要求：
- 写公众号、改公众号、做公众号选题、起标题、出大纲；
- 给现成文章做去 AI 味、压缩、改风格；
- 把 Markdown / 文档排版成微信公众号兼容 HTML；
- 生成公众号封面、正文配图；
- 推送到公众号草稿箱；
- 为「熵增时刻」或「思想的野路子丶」做内容生产。

**Don't use for:** 纯技术文档、纯图像生成、纯排版无公众号发布需求的任务。

## Output Contract

默认输出遵循下面的顺序：
1. 先给结果，不先讲长解释
2. 失败时先给失败原因，再给下一步建议
3. 生图成功后返回图片路径；图生图成功后返回编辑后图片路径
4. 不要自行扩展成额外流程，除非用户明确要求
5. 公众号场景下，优先保证可发，再优化细节

## Troubleshooting

封面或发布失败时按以下顺序排查：
1. **模板截图失败**：检查 HTML 变量是否正确填充，Playwright 是否正常启动
2. **Playwright 渲染命令超时/被 BLOCKED**：不要反复重试同一条截图命令；优先确认是否已有输出文件。若没有输出，为保交付可用 Pillow/PIL 生成轻量商业编辑风封面和正文信息图，保持尺寸契约（封面 900x383，正文图约 800 宽），再继续 `publish_pipe.py`。这属于临时保交付 fallback，后续再单独排查 Playwright。
3. **发布失败先保交付**：正文图或封面失败时，优先把正文、排版、草稿箱先走完
4. **format.py 图片丢失**：必须在运行排版前先创建 images/ 目录并放入图片
5. **封面路径错误**：封面生成后务必 `cp cover.png images/cover.png` 并用 `--cover` 参数显式指定

## 文章转写 / 二创改写规则

当用户转发公众号链接或现成文章并要求「改成我的风格」「推草稿箱」时，默认不是摘要，也不是大幅压缩，而是**同内容重写**：
- 保留原文主要内容、信息量和论证顺序，尽量像「同一篇文章的另一种表达方式」
- 按用户指定账号风格重写；熵增账号默认：像朋友聊天、多具体场景、结构清楚、中度改写
- 不出现原作者、原公众号、原推广卡片、原推荐阅读等来源信息
- 不直接使用原作者图片、视频、截图、解释图；如原文依赖这些素材，改为自制说明图、代码生成图、重新组织文字解释，或用新的封面/配图替代
- 去 AI 味必须在排版和发布前完成，避免公众号 AI 检测和限流风险
- 不要把「去 AI 味」误处理成「压缩摘要」；除非用户要求精简，否则保持原文 80% 左右的信息密度

## 封面与正文图规则

### 封面图
- 使用 HTML 模板填充（优先 `templates/editorial-cover-v2.html`），不再使用旧的浅色霓虹科技模板作为默认主方案，也不再调用 AI 生图
- 封面是标题的视觉引入口：通过大小、颜色、文字层级让读者一眼知道文章大概讲什么
- 默认采用 **商业编辑风（Business Editorial System）**：浅底纸面感、黑红蓝主色、大标题驱动、财经/商业媒体专题感
- 双账号在同一系统下做人格区分：熵增偏产业结构/权力地图，野路子偏资本牌桌/秩序博弈
- 仅在明确要求兼容旧稿时，才退回旧封面模板或历史样式
- 封面变量应尽量少，优先只保留：主标题、次标题、impact 数字、人格标签、少量关键词。不要继续增加新的重型变量。

### 正文图
- 默认使用 **商业编辑风信息图**（优先 `templates/editorial-body-v1.html`），不再默认使用旧的深色赛博组件库
- 正文图数量由内容决定，但必须按文章逻辑插入对应段落，禁止统一追加到文末
- 优先使用 4 类图型：总量级冲击图 / 人物-公司-市值卡 / 权力结构图 / 对照判断图
- 正文图应像财经/商业专题中的嵌入式信息图，而不是产品 dashboard 或发布会卡片
- 正文图交付前优先直接发图片给用户看效果
- 正文图的未来方向不是增加更多必填字段，而是减少每个模块的最小变量，改为“模块可组合、每张图只解决一个问题”的架构。

## 文章内正文图编排与视觉升级规则

### A. 正文图不能默认堆到文末
当正文图是为文章论证服务时，**默认要把图片插入对应段落之后，而不是统一 append 到全文末尾**。

强制规则：
- **人物/公司市值卡**：插在对应人物段落结束后，或该组人物分析段落结束后
- **结构图/权力地图**：插在总结性段落、结构性过渡段之后
- **总量级冲击图**：插在开头提出核心判断后，尽快出现，承担“首个视觉锚点”作用
- 除非用户明确要求“图放最后统一看”，否则不要把 3 张图统一堆到尾部

推荐插图节奏：
1. 开头结论段后 → 1 张总量级/总判断图
2. 中段人物或公司分析后 → 1 张人物/公司卡
3. 后段总结或结构升维段后 → 1 张结构图/关系图

### B. 正文图优先做“编辑型信息图”，不要默认赛博组件风
用户已明确反馈：旧版正文图虽然可用，但**不好看**，且深色赛博卡片风容易像“PPT 截图”或“脚本组件图”。

后续财经 / 产业 / 趋势 / 权力结构类文章，正文图默认优先使用：
- **商业杂志风 / 编辑型信息图 / 财经媒体内页图**
- 而不是深色霓虹 dashboard 风

默认视觉方向：
- 浅底或米白纸面底（如 `#F6F1E8` / `#F7F3EA`）
- 主字黑色，辅助深蓝、红色、金色做强调
- 大标题、大数字、大留白、粗分割线
- 字体更粗、更宽、更像“海报字”或“编辑标题字”
- 少用发光、毛玻璃、赛博网格、仪表盘感组件

### C. 财经/产业稿推荐的正文图组件
对这类文章，优先从下面 4 类里选，不要为了“模板覆盖率”硬上 6 大旧组件：
1. **总量级冲击图**
2. **人物-公司-市值卡**
3. **结构图 / 权力地图**
4. **对照关系图**

并新增执行原则：
- 正文图优先判断文章类型，再选模块，不再先定重模板再硬塞内容。
- 若一篇文章只需要 1～2 张图，不要为了流程完整性强行凑 3 张。

### D. 字体与方框字硬规则（2026-05 修复）

已实测踩坑：Headless Chromium / Playwright 在服务器环境中如果模板只写 `PingFang SC`、`Microsoft YaHei`、`Noto Sans CJK SC` 等字体名，但系统实际没有这些字体，中文会被渲染成“□”方框字。微信草稿箱看到封面/正文图全是框框时，根因通常是**截图阶段字体 fallback 失败**，不是 Markdown 或微信排版问题。

当前修复：
- `templates/editorial-cover-v2.html`
- `templates/editorial-body-v1.html`
- `templates/editorial-body-modular-v1.html`

均已内置：
```css
@font-face {
  font-family: "WQYZenHeiLocal";
  src: url("file:///usr/share/fonts/truetype/wqy/wqy-zenhei.ttc") format("truetype");
  font-display: block;
}
```
并把 `WQYZenHeiLocal` 放在 `font-family` 第一位。

同时 `render_editorial_cover.py` / `render_editorial_body.py` / `render_editorial_body_modular.py` 已改为 `wait_until="networkidle"`，并等待 `document.fonts.ready` 后再截图。

后续强制规则：
- 生成封面/正文图后，必须至少抽查一次图片本体；如果出现“□”方框字，不能发布，必须先修字体。
- 新增检测脚本：`scripts/check_image_tofu.py image1.png image2.png ...`，用于扫描疑似 tofu-box 缺字框。注意：该脚本基于边框/内部暗色比例检测，在正常中文图片上也有误报（阈值需调高或仅作辅助参考）。**视觉抽查（用 vision_analyze）仍是最可靠的验证方式。**
- 如果 Playwright 仍异常，立即回退到 PIL + `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc` 纯本地图，不要继续重试网页模板。
- 字体预检脚本内置了 `document.fonts.check('40px "WenQuanYi Zen Hei"', '中文测试美国AI')` 断言：如果系统字体不可用，截图前会直接报错而不是静默产出方框字图片。

### E. 用户人工换图场景
当用户明确说“图生成完直接发我，我来换”时：
- 不要重推草稿箱；
- 直接返回 `MEDIA:/absolute/path.png`；
- 同时说明已检查：无方框字、乱码、裁切。

## 模式选择 / 账号风格 / 协作规则 / 一键生产流程 / 其余工程细节

其余历史规则、发布命令、目录契约、坑点记录，继续以当前 skill 既有内容为准，不在本次 edit 中逐段重写；未来若继续重构，优先把新增规范外置到 references 与 scripts，而不是持续把所有实现细节堆回 SKILL.md。
