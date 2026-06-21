# 公众号图片中文字体方框排查与修复记录（2026-05）

## 触发信号

用户反馈：公众号草稿里的封面图、正文图中文全部/大量显示为方框（tofu 字符），即使本地重新推草稿后仍未改善。

## 根因

1. **HTML/Playwright 截图路径依赖浏览器字体 fallback**：模板 CSS 中的字体族在服务器/Chromium 环境里可能没有可用中文 glyph，中文会渲染成方框。
2. **PIL 也可能选错字体**：如果候选字体路径不存在或 fallback 到 DejaVuSans 等非中文字体，同样会出方框。
3. **只重做正文图不够**：封面图也可能来自同一类字体问题，必须同时检查封面和正文图。
4. **重推草稿不能证明修复**：如果微信草稿仍引用旧上传素材，或本地修复没有覆盖所有图片，用户看到的仍是方框。

## 推荐修复策略

### 1. 先确认系统中文字体

```bash
fc-list :lang=zh | head -50
```

当前环境可用字体示例：

```text
/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
/usr/share/fonts/opentype/unifont/unifont.otf
```

优先使用：

```text
/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
```

### 2. 用 Hermes venv 运行 PIL 检查字体

系统 python 可能没有 PIL；优先：

```bash
~/.hermes/hermes-agent/venv/bin/python3 - <<'PY'
from PIL import ImageFont
p='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
f=ImageFont.truetype(p,40)
print(f.getbbox('美国AI政策的四股力量'))
print(f.getmask('美国').getbbox())
PY
```

若 bbox 正常且非空，说明字体可绘制中文。

### 3. 紧急交付时，绕开 HTML/Playwright，直接用 PIL 绘制 PNG

关键点：
- 强制 `ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', size)`
- 不使用默认字体
- 封面和正文图都重做
- 生成后直接发图片给用户让其人工替换，不要先重推草稿

### 4. 验证方式

- 用 `file path.png` 确认尺寸与 PNG 有效。
- 可以人工/视觉检查本地 PNG 是否还有方框、乱码、裁切。
- 但用户已经要求“生图后直接发图给用户”时，不要再依赖视觉分析作为交付判断；直接发送图片，用户自行判断。

## 工作流纠正

当用户说“正文图/封面图都是框框、没改变”时：

1. 停止继续重推草稿。
2. 排查字体源和渲染路径。
3. 同时重做封面图和正文图。
4. 明确输出文件路径。
5. 在回复中用 `MEDIA:/absolute/path.png` 直接发图给用户。

## 已知坑

- `identify` 可能未安装，不能依赖 ImageMagick。
- 系统 `python3` 可能没有 PIL，优先 Hermes venv。
- Playwright 截图即使模板正确，也可能因为浏览器中文字体 fallback 失败出现方框。
- 微信草稿里的旧图片可能不会因本地文件覆盖而自动变化；用户要求看图时，直接发新文件最稳。
