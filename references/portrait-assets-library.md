# 人物素材库使用指南

## 概述

人物素材库用于存放可复用的肖像图片，供公众号文章封面和正文图使用。

**路径：** `~/.hermes/assets/portraits/`

**索引文件：** `INDEX.md` — 列出所有素材及其属性（人物、风格、场景、尺寸、用途建议）

## 当前素材

| 文件名 | 人物 | 风格 | 场景 |
|--------|------|------|------|
| `musk-color-hero.png` | 马斯克 | 彩绘海报 | 科技企业家+火箭背景 |
| `jensen-gpu-launch.png` | 黄仁勋 | 厚涂油画 | 发布会手持显卡 |
| `jensen-ai-domination.png` | 黄仁勋 | 电影海报 | 手掌掌控四家AI图标 |

## 引用方式

### 正文图注入

Markdown 中插入：
```markdown
<!-- img: hero ~/.hermes/assets/portraits/jensen-gpu-launch.png -->
```

发布时通过 `--images` 参数传递给 `publish_pipe.py`。

### 封面图

```bash
python3 scripts/run.py publish_pipe.py \
  --cover ~/.hermes/assets/portraits/jensen-ai-domination.png \
  ...
```

## 使用场景

- 人物专访、公司动态、产业分析类文章
- 根据文章主题选择匹配风格的素材
- 彩绘海报偏科技叙事感；厚涂油画偏发布会/新闻感

## 扩展素材

新增素材时：
1. 生成图片并保存到 `~/.hermes/assets/portraits/`
2. 文件命名：`人物-场景/风格.png`（英文极简）
3. 更新 `INDEX.md` 添加新条目
4. 同步更新 memory 中的素材库路径信息

## 与生图技能配合

当用户要求生成人物图并加入素材库时：
1. 先用 `gpt-image-generator` 生成图片
2. 询问用户是否满意，确认后加入素材库
3. 更新 INDEX.md 并告知用户命名和用途建议