# Cron Prompt ↔ Skill 同步记录

> 当 cron 定时任务提示词大版本升级时，skill 侧必须同步检查，否则 agent 执行时会同时看到两套不一致的规则。
> 本文件记录 2026-07-04 v2→v3.0 升级时发现的冲突和修复方式，作为未来版本升级的参考。

## v3.0 升级时的 4 处冲突（2026-07-04 全部修复）

### 1. 账号人设不一致（yeluzi）

- **冲突**：SKILL.md 写"资本牌桌、冲突感、情绪推进"；AGENTS.md 写"capital, conflict, emotional momentum"；v3.0 prompt 写"民生、消费、职场、不煽情、不站队"。
- **修复**：SKILL.md 和 AGENTS.md 都更新为 v3.0 的定位。同时修正了旧版"双账号共享一套配图"规则——改为各自独立配图。
- **教训**：升级 prompt 中的账号定位后，必须同步检查 SKILL.md 写作快路径的双账号差异段、AGENTS.md 的"Two accounts"段。三处必须一致。

### 2. AI 辅助标识范围歧义

- **冲突**：v3.0 规则 15 原文"草稿报告中必须提醒…按平台要求完成必要声明或标识"可能被理解为"文章正文里加 AI 声明"，与 `publish_pipe.py` 的 AI 身份披露硬门禁冲突。
- **修复**：改为"报告层提醒运营者复核（非文章正文）"，并加"⚠️ 文章正文/封面/图片中严禁 AI 身份披露（publish_pipe.py 硬门禁拦截）"。
- **教训**：prompt 中任何涉及"AI 辅助"的措辞，必须区分"报告/消息层"和"文章内容层"。用户的长期禁令是文章里绝不出现 AI 披露。

### 3. 旧版 cron 提示词参考文件残留

- **冲突**：`references/cron-prompts-2026-06.md` 存的是 v2 提示词，SKILL.md 引导 agent 去读它。cron 执行时 agent 同时看到 v3.0（jobs.json）和 v2（references/），被旧规则干扰。
- **修复**：删除该文件，清理 SKILL.md 中全部 3 处引用。cron prompt 唯一真相源是 `~/.hermes/cron/jobs.json`。
- **教训**：cron prompt 不要在 skill 目录里建参考副本——两份会 drift。只有 jobs.json 是 source of truth。

### 4. 发布命令模式（--dir vs --input --job-dir）

- **冲突**：v3.0 沿用 `--dir` 模式，但 SKILL.md 推荐 cron 用 `--input --job-dir`（自动处理 format.py 输出结构，避免 `article.html` 位置陷阱）。
- **修复**：v3.0 prompt 中所有 dry-run 和正式发布命令都改为 `--input --job-dir` 模式，路径参数全部用绝对路径。
- **教训**：prompt 中的发布命令必须和 SKILL.md 推荐的 cron 最简路径一致。

## 未来升级检查清单

升级 cron prompt（v3→v4 或任何大改）时，按以下 4 步检查 skill 侧：

1. **账号人设三处一致**：SKILL.md 双账号差异段 + AGENTS.md "Two accounts" 段 + prompt 中的定位描述。
2. **AI 标识措辞**：prompt 中"AI 辅助"相关措辞只在报告层，不触碰文章正文硬门禁。
3. **无参考副本**：skill 目录里不存 cron prompt 副本，jobs.json 是唯一真相源。
4. **发布命令模式**：prompt 中的 `publish_pipe.py` 命令用 `--input --job-dir`，路径参数全绝对。

## 冲突消解优先级

`prompts/quality-and-risk.md` > skill `SKILL.md` > cron 提示词。

cron 提示词是任务指令，skill 是能力边界。提示词可以更严格但不能突破 skill 的硬门禁（如 AI 披露拦截、高风险关键词扫描）。

## v3.1 反低创作度同步（2026-07-06）

### 触发原因

微信低创作度示例明确会检测同一账号近期内容是否主题、标题、正文框架、封面高度相似。v3.0 虽然解决了单源洗稿、标题党和高风险角度，但把正文写作固化为“标题 → 开头 → 事实底座 → 背景解释 → 原创分析 → 普通人影响 → 中国变量 → 结尾”，封面也容易变成 Swiss/baoyu 同模板换字，仍会形成“框架一致”的批量内容信号。

### 同步改动

- `quality-and-risk.md`：去同质化从“双账号同日不同题”升级为“同账号近 7 天结构、标题、封面、正文图都要避重”。
- `SKILL.md`：账号“优先结构”改为“常用但不固定的组织方式”；Swiss Minimal 降级为备用封面；正文图禁止默认固定 baoyu-comic + dramatic/neutral。
- `cron-prompts/*.md`：正文“结构 1-9”改为“必备信息组件 + 结构原型菜单”；封面改为多原型轮换；报告和 publish-history 记录结构/视觉指纹。
- `publish_pipe.py` / `publish_history.py`：发布时记录结构签名，并对同账号近期历史做低创作度相似性 warning。

### 未来升级检查

升级 cron prompt 时，必须搜索是否重新出现以下固定模板信号：

- “结构：1. 标题 2. 开头 3. 事实底座 ...”
- “优先结构：A → B → C → D”
- “封面默认用 Swiss Minimal”
- “风格 baoyu-comic，情绪 dramatic/neutral，尺寸 1024x576”

这些写法只能作为候选之一，不能作为每日默认结构。

## v3.2 compact 轻量化同步（2026-07-06）

### 触发原因

v3.1 解决了固定结构和视觉重复，但两个 cron prompt 仍各自复制了一整套质量规则、来源分级、标题规则、正文规则、封面规则和自检规则。定时任务执行时又会加载 `SKILL.md` 与 `quality-and-risk.md`，导致上下文过重，并增加模型抓住长模板复读的概率。

### 同步改动

- `cron-prompts/cron-morning-xiaocong.md` 与 `cron-prompts/cron-evening-yeluzi.md` 改为 compact 形态：只保留任务差异、执行流程、产物要求、发布命令和报告字段。
- 通用质量规则不再复制到 cron prompt；统一由 `prompts/quality-and-risk.md`、`SKILL.md` 和发布脚本维护。
- 保留质量底线：多源、信息增量、同账号近 7 天去重、视觉元数据、dry-run、草稿箱推送路径都仍在 compact prompt 中显式要求。
- 定时任务发布命令保留 `--fail-on-low-quality-warning`，把发布脚本的低创作度相似性 warning 升级为无人值守场景下的停止条件；人工临时发布仍可不加该参数。

### 未来升级检查

不要把 `quality-and-risk.md` 的完整内容再粘回 cron prompt。cron prompt 应该像任务控制面板，不是写作规则全集。升级发布命令时不要删掉 `--fail-on-low-quality-warning`。
