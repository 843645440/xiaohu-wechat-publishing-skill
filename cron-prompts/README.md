# 定时任务提示词（Cron Prompts）

本目录存放公众号双账号定时草稿箱工作流的完整提示词。

## 用途

这两个提示词是 Hermes cron 定时任务（`~/.hermes/cron/jobs.json`）实际执行的 prompt。
每个定时任务启动时，agent 会加载 `xiaohu-wechat-publishing` skill + 对应提示词，然后按提示词中的流程完成选题、写作、配图、自检、推送草稿箱。

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

两个提示词共享大部分规则（v3.0），差异在：
1. **账号定位和写作风格**（第十四节）
2. **选题方向**（早间偏科技产业，晚间偏民生消费）
3. **job 目录路径**（`-am/xiaocong/` vs `-evening/yeluzi/`）
4. **互斥检查**（晚间需检查早间选题避免撞题）

共享规则包括：最高优先级规则、中国变量规则、爆款选题原则、四层信息要求、来源分级、候选评分、高风险淘汰、标题规则、正文写作、封面配图、发布前自检 A-I、publish-history 记录、禁止内容类型。

## 升级提示词时的检查清单

参见 `references/cron-prompt-sync-2026-07.md`，升级时需要同步检查：
1. 人设/账号风格是否一致
2. AI 标识规则是否正确
3. 发布命令路径是否正确
4. 无副本规则（正文中不出现 AI 身份披露）
