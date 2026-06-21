# 正文图生成：baoyu 框架 + Agnes API 实操

## 流程

1. 读完文章，确定 1-2 个图位（解释型或轻讽刺型）
2. 用 ZONES / LABELS / COLORS / STYLE / ASPECT 框架组织视觉构思
3. 将框架转化为一段 Agnes 可执行的英文 prompt（LABELS 中的中文主题词最多 1-2 个）
4. 调用 Agnes API 生成 1024x576 宽图
5. 两个账号共用配图，不分别生成

## 框架结构

```
ZONES: 画面分区布局（哪些区域放什么元素）
LABELS: 画面中出现的文字元素（中文最多 1-2 个主题词，其余用英文/符号）
COLORS: 配色方案
STYLE: 渲染风格（manga + dramatic/neutral/warm 等）
ASPECT: 比例（默认 16:9 横图）
```

## 完整示例：百亿补贴配图

**分析**：文章核心张力是"百亿补贴的成本到底谁在承担"，三方信息不对称。

**图位 1 - 解释型（dramatic tone）**

框架：
- ZONES: 顶部红色横幅"百亿补贴"；下方三个分镜：消费者拿优惠券微笑/商家钱包漏水/平台坐高处收金币
- LABELS: 百亿补贴（唯一中文）；其余用箭头、问号、金币图标表达
- COLORS: 深蓝 #1e3a5f + 红色 #c1272d 强调 + 浅灰背景
- STYLE: manga + dramatic, bold ink lines, screentone shading, knowledge comic
- ASPECT: 16:9 landscape

Agnes prompt 输出：
```
Knowledge comic manga style, 16:9 landscape wide format. Dramatic tone.
Top banner with bold text 百亿补贴 in red calligraphy.
Below: three manga panels in sequence.
Left panel: happy consumer holding shopping bags, sparkle effects,
but dark shadow shows question marks.
Middle panel: sweating merchant with draining wallet,
money flowing upward through visible pipe.
Right panel: large platform figure sitting high,
collecting coins and data charts, confident expression.
Bold ink lines, screentone shading, dramatic contrast.
Visual storytelling without dialogue bubbles.
Red and dark blue color palette.
```

**图位 2 - 轻讽刺型（warm tone）**

框架：
- ZONES: 消费者站在巨大手机屏幕前，屏幕满屏"百亿补贴"红色标签，手拿放大镜凑近看
- LABELS: 百亿补贴（唯一中文）；放大镜下隐约可见的小字用视觉模糊表达，不写具体文字
- COLORS: 暖色调为主，红色标签 vs 褪色灰色背景形成反差
- STYLE: manga + warm, gentle ink lines, concept-story visual metaphor
- ASPECT: 16:9 landscape

Agnes prompt 输出：
```
Knowledge comic manga style, 16:9 landscape wide format. Warm tone.
Title text 百亿补贴 in red at top.
Scene: A consumer character standing in front of a giant smartphone screen
displaying many red sale tags.
The character holds a magnifying glass, examining closely.
Behind the red tags, faint blurry elements hint at hidden conditions.
The consumer has a surprised awakening expression, eyes wide.
Warm manga screentone, gentle ink lines.
Background: mountains of coupons fading from vibrant red to muted gray.
Concept-story visual metaphor. No dialogue bubbles.
```

## Agnes API 调用模板

```bash
RESPONSE=$(curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "<上面构造好的 prompt>",
    "size": "1024x576",
    "n": 1
  }' 2>/dev/null)
URL=$(echo $RESPONSE | jq -r '.data[0].url')
curl -sSL --max-time 60 "$URL" -o /absolute/path/to/body-image.png
```

## 关键注意

- prompt 主体用英文写，中文只保留画面中必须出现的 1-2 个主题词
- 不要写 "Chinese text labels" 之类的指令让模型去生成多行中文
- 不要用对话框文字、标签文字等需要精确中文的场景
- 如果需要精确中文文字，用 Python/PIL 后期叠加到图片上
- baoyu-comic skill 提供 art style 和 tone 的组合参考，但最终 prompt 要转化为 Agnes 可执行的英文描述
