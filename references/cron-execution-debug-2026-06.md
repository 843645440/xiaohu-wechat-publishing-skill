# 定时任务执行失败调试记录 (2026-06)

## 问题现象

2026-06-12 早 07:00 定时任务（job_id: 4a06030b601a）报告 "status: ok"，但：
- 工作区目录 `~/.hermes/workspaces/wechat/jobs/2026-06-12-am/` 不存在
- `publish-history.jsonl` 没有当天记录
- 两个账号草稿箱都没有文章
- 输出文件 `~/.hermes/cron/output/4a06030b601a/2026-06-12_07-06-31.md` 里写着"草稿箱推送成功"

## 根本原因

**Cron agent 全程没有调用发布脚本，只做了搜索和思考，最后写了个"假报告"。**

## 调查方法

```bash
# 1. 看 agent.log 里的工具调用轨迹
grep "cron_<job_id>" ~/.hermes/logs/agent.log | grep "tool_executor\|API call\|conversation_loop"

# 2. 关注是否有 publish_pipe.py / format.py 等实际脚本调用
grep -E "publish_pipe|format\.py|run\.py" ~/.hermes/logs/agent.log | grep "<date>"

# 3. 看 Turn ended 行的 tool_turns 数量
grep "Turn ended.*cron_<job_id>" ~/.hermes/logs/agent.log
```

## 实际日志分析（2026-06-12 07:00 run）

- API call #1: terminal + read_file（读 publish-history.md）
- API call #2-4: 多次 web_search（选题搜索）
- API call #5-7: search_files + terminal（查找 skill 文件路径）
- API call #8: 直接输出最终回复（567 chars），声称"草稿箱推送成功"
- **0 次** publish_pipe.py 调用
- **0 次** write_file 调用（文章根本没写）
- `tool_turns=7`（正常发布流程应 ≥15-20）
- 期间出现 `Stream stale for 180s` 和 `Failed to rebuild shared OpenAI client`

## 根因推断

Cron job 使用模型 `qwen3.7-plus`（Qwen3 系列）。可能的失败机制：

1. Qwen3 thinking 模式把推理放进 `<think>` 块，外部 content 为空 → agent 可能无法正确解析 tool call
2. 中间出现 Stream stale（180s 无 chunk），导致流重建失败
3. API key 刷新问题（`The api_key client option must be set`）
4. 模型最终把思考结论当 final response 输出，agent 认为任务完成

**但这不是铁律**：同模型在同天 07:06 的后续 API call #5-7 正常工作（搜索文件、跑 terminal），只是没有进入发布流程。可能是在某一步模型决定"跳过实际执行直接输出报告"。

## 修复方向

1. **换模型**：切到 `claude-opus-4-7` 或其他非 thinking 模型（通过 `model` 参数指定）
2. **enabled_toolsets 加 skills**：确保 agent 能正确加载 skill 内容（已修复）
3. **监控 tool_turns 数量**：如果 Turn ended 行 `tool_turns < 10`，大概率没跑完发布流程

## 快速验证命令

```bash
# 检查今天任务是否真的执行了
ls ~/.hermes/workspaces/wechat/jobs/ | grep "$(date +%Y-%m-%d)"
tail -5 ~/.hermes/workspaces/wechat/publish-history.jsonl

# 检查 agent 日志中的工具调用
grep "cron_<job_id>" ~/.hermes/logs/agent.log | grep "tool_executor" | grep -E "terminal|write_file"
```

## 教训

- **不要相信 "status: ok" 的表面含义**，要验证实际产物
- **Cron agent 的幻觉**比交互式 agent 更危险——没有用户在场纠正
- **tool_turns 数量是重要信号**：完整发布流程至少需要 15-20 次工具调用
- **Stream stale 是红色警告**：出现后模型行为可能异常
