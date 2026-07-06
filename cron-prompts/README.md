# 定时任务提示词（Cron Prompts）

本目录存放公众号双账号定时草稿箱工作流提示词。

## 用途

这两个提示词是 Hermes cron 定时任务（`~/.hermes/cron/jobs.json`）实际执行的 prompt 副本。
每个定时任务启动时，agent 会加载 `xiaohu-wechat-publishing` skill + 对应提示词，然后按提示词中的紧凑流程完成选题、写作、配图、自检、推送草稿箱。

## 文件说明

| 文件 | 对应 cron job | 账号 | 执行时间 | 定位 |
|------|--------------|------|---------|------|
| `cron-morning-xiaocong.md` | `daily-wechat-hotspot-morning-global` (ID: 4a06030b601a) | xiaocong（熵增时刻） | 每天北京时间 07:00 | 科技/产业/AI/公司变化 |
| `cron-evening-yeluzi.md` | `daily-wechat-hotspot-evening-domestic` (ID: 440cf95e75c7) | yeluzi（思想的野路子丶） | 每天北京时间 17:00 | 民生/消费/职场/平台规则 |

## 与 jobs.json 的关系

- **唯一真相源是 `~/.hermes/cron/jobs.json`**（cron 系统从这里读 prompt 执行）。
- 本目录的副本用于：版本管理、代码审查、skill 整体打包分发、离线阅读。
- 修改提示词时，**必须同步更新** `jobs.json` 和本目录副本，保持一致。

## 提示词核心内容

两个提示词从 v3.2 开始采用 compact 形态：cron prompt 只保留任务差异和执行顺序，质量、安全、去同质化、视觉规则由 `SKILL.md`、`prompts/quality-and-risk.md` 和发布脚本承担。

差异在：
1. **账号定位和写作风格**（第十四节）
2. **选题方向**（早间偏科技产业，晚间偏民生消费）
3. **job 目录路径**（`-am/xiaocong/` vs `-evening/yeluzi/`）
4. **互斥检查**（晚间需检查早间选题避免撞题）

共享规则不要在 cron prompt 里重复粘贴。需要改通用质量规则时，优先改 `prompts/quality-and-risk.md`；需要改运行路径或硬门禁时，优先改 `SKILL.md` 和脚本。

注意：共享规则不是共享固定文章模板。两个任务都要求先比对同账号近 7 天历史，再选择正文结构原型、标题句式、封面原型和正文图类型，避免短期内出现框架一致、封面同模板换字、正文图同风格重复等低创作度信号。

cron 发布命令必须保留 `--fail-on-low-quality-warning`：发布脚本默认只 warning，定时任务需要把同账号近期结构/视觉相似性命中升级为停止条件，避免无人值守时继续推送疑似低创作度草稿。

## 升级提示词时的检查清单

参见 `references/cron-prompt-sync-2026-07.md`，升级时需要同步检查：
1. 人设/账号风格是否一致
2. AI 标识规则是否正确
3. 发布命令路径是否正确
4. 发布命令是否保留 `--fail-on-low-quality-warning`
5. 无副本规则（正文中不出现 AI 身份披露）
