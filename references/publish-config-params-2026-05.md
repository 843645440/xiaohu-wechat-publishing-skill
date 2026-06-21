# 发布配置参数说明

## 概述

`publish_pipe.py` 草稿箱发布接口的关键参数配置。对应微信官方 `draft/add` 接口。

## 当前配置（自动注入）

### 评论设置

| 参数 | 值 | 说明 |
|------|-----|------|
| `need_open_comment` | `1` | 打开评论功能 |
| `only_fans_can_comment` | `1` | 仅粉丝可评论 |

### 作者配置

通过环境变量按账号区分，无需手动传入：

| 账号 | 环境变量 | 值 |
|------|----------|-----|
| `xiaocong` | `WECHAT_AUTHOR_XIAOCONG` | `熵增时刻` |
| `yeluzi` | `WECHAT_AUTHOR_YELUZI` | `思想的野路子丶 |

环境变量定义在 `~/.hermes/.env`。

### 摘要配置

`publish_pipe.py` 自动从 HTML 正文提取摘要：

- 函数：`extract_digest_from_html(html)`
- 逻辑：剥离 HTML 标签 → 合并空白 → 截取前 54 字符
- 官方限制：≤128 字符

## 调用示例

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --account xiaocong
```

作者、摘要、评论设置均自动处理，无需额外参数。

## 参数来源

根据微信官方 `api_draft_add.html` 文档实现：

- `author`：从 `.env` 按账号读取
- `digest`：自动提取正文前 54 字
- `need_open_comment`：硬编码 `1`
- `only_fans_can_comment`：硬编码 `1`

## 待扩展参数

以下参数当前未启用，可按需添加：

- `content_source_url`：原文链接（转载场景）
- `pic_crop_235_1` / `pic_crop_1_1`：封面精确裁剪