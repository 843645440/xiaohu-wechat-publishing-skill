# 定时任务提示词

本目录存放 Hermes cron prompt 的维护副本。真实运行配置仍需同步到 Hermes cron。

| 文件 | 账号 | 执行时间 | 定位 |
|---|---|---|---|
| `cron-morning-xiaocong.md` | xiaocong（熵增时刻） | 每天北京时间 07:00 | 科技/产业/AI/公司变化 |
| `cron-evening-yeluzi.md` | yeluzi（思想的野路子丶） | 每天北京时间 17:00 | 民生/消费/职场/平台规则 |

## v4.1 information-first 原则

- Cron prompt 只保留任务差异和执行顺序，不复制长规则。
- 写作前读 `prompts/quality-and-risk.md` 和 `prompts/markdown-elements.md`。
- 写稿前写简短的 `source-notes.md`，记录事实及来源；它只属于当次 job，不进入长期历史。
- 初稿后先做删除式空话检查，再进入 humanizer。
- 初稿后必须使用外部 `humanizer` skill，并保存 `article.raw.md`、`article.md`、`humanizer-report.md`。
- 配图前只读 `references/visual-generation-light.md`；不要读取封面预设池、人物资产说明或旧视觉文档。
- 防重只看近期标题和文章大意。
- 报告只输出标题、大意、来源数量、去 AI 味结果、视觉结果、发布结果和产物路径。
- 不做 OCR、识图、图片相似度或视觉评分。

## 发布命令

Cron 命令必须保留 `--fail-on-low-quality-warning`。它现在表示“近期标题/文章大意相似则停止”，不是旧版结构/视觉签名防重。

## 不要恢复的旧规则

- 不要恢复固定结构分析字段。
- 不要恢复长篇报告模板。
- 不要读取完整视觉风格库或外部写作/视觉 skill。
- 不要恢复正文 HTML 生图脚本、图片相似性检查或视觉审核步骤。
- 不要把旧设计文档或排障长文重新挂到默认流程里。
