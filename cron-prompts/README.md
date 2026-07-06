# 定时任务提示词

本目录存放 Hermes cron prompt 的维护副本。真实运行配置仍需同步到 Hermes cron。

| 文件 | 账号 | 执行时间 | 定位 |
|---|---|---|---|
| `cron-morning-xiaocong.md` | xiaocong（熵增时刻） | 每天北京时间 07:00 | 科技/产业/AI/公司变化 |
| `cron-evening-yeluzi.md` | yeluzi（思想的野路子丶） | 每天北京时间 17:00 | 民生/消费/职场/平台规则 |

## v4.0 lightweight 原则

- Cron prompt 只保留任务差异和执行顺序，不复制长规则。
- 写作前读 `prompts/quality-and-risk.md` 和 `prompts/markdown-elements.md`。
- 初稿后必读 `references/humanizer-runtime.md`。
- 配图前必读 `references/visual-generation-light.md`。
- 防重只看近期标题和文章大意。
- 报告只输出标题、大意、来源数量、去 AI 味结果、视觉结果、发布结果和产物路径。

## 发布命令

Cron 命令必须保留 `--fail-on-low-quality-warning`。它现在表示“近期标题/文章大意相似则停止”，不是旧版结构/视觉签名防重。

## 不要恢复的旧规则

- 不要恢复固定结构分析字段。
- 不要恢复长篇报告模板。
- 不要读取完整视觉风格库或外部写作/视觉 skill。
- 不要把旧设计文档或排障长文重新挂到默认流程里。
