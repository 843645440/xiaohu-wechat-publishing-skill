# 公众号脚本运行时依赖与临时回退记录（2026-05）

本次实测得到的两个关键运行时结论：

## 1) 优先使用 Hermes venv Python

运行公众号脚本时，优先使用：

```bash
~/.hermes/hermes-agent/venv/bin/python3
```

原因：
- 系统 `python3` 可能缺少 `markdown` 等依赖，导致 `format.py` 直接报错
- Hermes venv 中通常已经具备公众号脚本所需的依赖

推荐调用方式：

```bash
PY=~/.hermes/hermes-agent/venv/bin/python3
$PY ~/.hermes/skills/xiaohu-wechat-publishing/scripts/publish_pipe.py \
  --input /path/to/article.md \
  --cover /path/to/cover.png \
  --account xiaocong
```

## 2) 封面脚本可能依赖 Playwright

`render_editorial_cover.py` 在当前环境下可能因缺少 `playwright` 退出。

### 处理策略
- 如果封面脚本可用：继续用正式模板生成
- 如果当前环境缺依赖、但必须立刻发草稿：
  - 临时改用纯本地 SVG / HTML 方案生成封面图
  - 再将产物交给 `publish_pipe.py` / `publish.py`

### 经验教训
- 封面失败不应阻塞整个发布链路
- 先保证“能进草稿箱”，再回头修封面生成依赖
- 一旦发现脚本依赖漂移，应把实际可运行的 Python 解释器和回退方案写进技能库
