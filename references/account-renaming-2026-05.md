# 账号重命名记录（2026-05-14）

## 变更
- **旧名**：小葱AI社 → **新名**：熵增时刻
- **简称**：小葱 → 熵增
- **内部代号不变**：`xiaocong`（env 变量 `WECHAT_APPID_XIAOCONG`、`--account xiaocong`）
- **app_id 不变**：`wx6e2f6e96fc2b5b35`

## 全局替换范围
活跃文件中已替换完成（sessions 日志为只读，保留旧名不影响）：
- `SKILL.md`、`references/*.md`、`scripts/*.py`、`.env`（author 字段）、`memories/`

## 清理注意
垃圾清理时 **不要删除** `templates/preview.html`（format.py 依赖它）。
