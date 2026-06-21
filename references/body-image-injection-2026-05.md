# 正文图注入模式（2026-05 实测）

## 核心规则

1. **Marker 格式**：`<!-- img: hero /path/to/image.png -->` 或 `<!-- img: filename.png -->`
2. **搜索路径优先级**：
   - Markdown 同目录的 `images/` 子目录
   - `--output-dir` 下的 `images/`
   - 当前工作目录
   - **不在上述路径时，必须用 `--images` 参数显式指定**

## 常见场景

### 场景 1：图片在 Markdown 同目录

```bash
# 目录结构
# article.md
# images/hero.png
python3 scripts/run.py publish_pipe.py --input article.md --cover cover.png --account xiaocong
# 无需 --images，自动找到 images/hero.png
```

### 场景 2：图片在其他位置（如 /tmp）

```bash
# Marker: <!-- img: hero /tmp/generated_image.png -->
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --images /tmp/generated_image.png \
  --account xiaocong
# --images 参数必须指定，否则 dry-run 报 "找不到图片"
```

### 场景 3：多张正文图

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --images /tmp/img1.png /tmp/img2.png \
  --account xiaocong
```

## dry-run 校验

```bash
python3 scripts/run.py publish_pipe.py \
  --input article.md \
  --cover cover.png \
  --images /path/to/body.png \
  --account xiaocong \
  --dry-run
```

成功输出：
```
=== 第二步：图片注入 ===
  ✓ 标记替换: 1 处
  HTML 中共 1 个 <img> 标签
```

失败输出：
```
=== 第二步：图片注入 ===
  ⚠ 找不到图片: 1 个 → hero /tmp/xxx.png
```

## 注入后的文件结构

```
manual-format/article-name/
  article.html      # 注入后的 HTML
  preview.html      # 预览页面
  images/
    xxx.png         # 图片被复制到此目录
```

HTML 中的 `<img>` src 会变成 `images/xxx.png`（相对路径），上传时自动替换为微信 media URL。