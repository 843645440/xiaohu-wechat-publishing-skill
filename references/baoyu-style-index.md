# Baoyu 配图风格索引（公众号自动匹配用）

公众号配图时，根据文章内容自动从以下三个 baoyu skill 中选择最合适的风格组合。
生成模型统一使用 **Agnes Image 2.1 Flash**（`agnes-image-2.1-flash`）。

---

## 一、三大配图 Skill 概览

| Skill | 适用场景 | 核心维度 |
|-------|---------|---------|
| **baoyu-article-illustrator** | 文章配图（信息图、场景、流程图、对比、框架、时间线） | Type × Style × Palette |
| **baoyu-comic** | 知识漫画（叙事、传记、教程、概念解释） | Art × Tone × Layout |
| **baoyu-infographic** | 高密度信息图（数据可视化、结构化总结） | Layout × Style |

---

## 二、baoyu-article-illustrator 风格库

### 2.1 Type（信息结构）

| Type | 适用内容 |
|------|---------|
| `infographic` | 数据、指标、技术概念 |
| `scene` | 叙事、情感、生活场景 |
| `flowchart` | 流程、步骤、工作流 |
| `comparison` | 对比、选项、前后对照 |
| `framework` | 模型、架构、系统关系 |
| `timeline` | 历史、演化、里程碑 |

### 2.2 Style（渲染风格）

| Style | 视觉特征 | 最佳搭配 Type |
|-------|---------|--------------|
| `vector-illustration` | 扁平矢量、粗线条、几何图标 | infographic, flowchart, comparison, framework |
| `notion` | 极简手绘线条、柔和图标 | infographic, flowchart（SaaS/生产力） |
| `elegant` | 精致、高级感 | comparison, framework, timeline（商务/思想领导力） |
| `warm` | 友好、温暖、金色光线 | scene, timeline（个人成长/生活） |
| `minimal` | 极简、禅意 | infographic, framework（哲学/核心概念） |
| `blueprint` | 技术蓝图、网格、等宽字体 | infographic, framework, flowchart（架构/系统设计） |
| `watercolor` | 水彩、柔和边缘、艺术感 | scene（生活/旅行/创意） |
| `editorial` | 杂志风信息图 | infographic（新闻/数据报道） |
| `scientific` | 学术精确图表 | infographic（生物/化学/科研） |
| `screen-print` | 丝网印刷、有限色、半调纹理 | scene, comparison（观点/文化/电影感） |
| `ink-notes` | 黑墨水+稀疏语义色、手绘笔记 | comparison, flowchart, framework（宣言/前后对比/技术笔记） |
| `sketch-notes` | 柔和手绘笔记、温暖感 | flowchart（教育/温暖笔记） |
| `chalkboard` | 黑板粉笔 | infographic（教学/解释） |
| `fantasy-animation` | 吉卜力/迪士尼手绘 | scene（故事/魔法/情感） |
| `pixel-art` | 复古 8-bit | infographic（游戏/复古科技） |
| `retro` | 80/90 年代霓虹几何 | infographic（怀旧/大胆） |
| `vintage` | 做旧羊皮纸 | timeline（历史/遗产） |

### 2.3 Palette（调色板，可覆盖 Style 默认配色）

| Palette | 配色特征 | 适用场景 |
|---------|---------|---------|
| `macaron` | 柔和粉彩（蓝/薄荷/薰衣草/桃）+ 暖奶油底 | 教育/知识/教程 |
| `warm` | 暖大地色（橙/赤陶/金）+ 桃底，无冷色 | 品牌/产品/生活 |
| `neon` | 霓虹（粉/青/黄）+ 深紫底 | 游戏/复古/流行文化 |
| `mono-ink` | 黑白+稀疏语义色（珊瑚红/青绿/薰衣草） | 专业视觉笔记/前后对比/宣言 |

### 2.4 Preset（预设组合）

| Preset | Type + Style + Palette | 适用内容 |
|--------|----------------------|---------|
| `tech-explainer` | infographic + blueprint | API 文档、系统指标、技术深度 |
| `system-design` | framework + blueprint | 架构图、系统设计 |
| `architecture` | framework + vector-illustration | 组件关系、模块结构 |
| `knowledge-base` | infographic + vector-illustration | 概念解释、教程、how-to |
| `saas-guide` | infographic + notion | 产品指南、SaaS 文档 |
| `tutorial` | flowchart + vector-illustration | 步骤教程、设置指南 |
| `process-flow` | flowchart + notion | 工作流文档、入职流程 |
| `edu-visual` | infographic + vector-illustration + macaron | 知识总结、概念解释、教育 |
| `hand-drawn-edu` | flowchart + sketch-notes + macaron | 手绘教育图、流程解释 |
| `ink-notes-compare` | comparison + ink-notes + mono-ink | 前后对比、传统 vs 新、宣言 |
| `ink-notes-flow` | flowchart + ink-notes + mono-ink | 专业流程解释、技术笔记 |
| `ink-notes-framework` | framework + ink-notes + mono-ink | 系统类比、架构图、技术宣言 |
| `data-report` | infographic + editorial | 数据新闻、指标报告 |
| `versus` | comparison + vector-illustration | 技术对比、框架对决 |
| `business-compare` | comparison + elegant | 产品评估、策略选项 |
| `storytelling` | scene + warm | 个人散文、反思、成长故事 |
| `lifestyle` | scene + watercolor | 旅行、健康、生活、创意 |
| `history` | timeline + elegant | 历史概览、里程碑 |
| `evolution` | timeline + warm | 进步叙事、成长旅程 |
| `opinion-piece` | scene + screen-print | 评论、批判性文章 |
| `editorial-poster` | comparison + screen-print | 辩论、对比观点 |
| `cinematic` | scene + screen-print | 戏剧叙事、文化文章 |

---

## 三、baoyu-comic 风格库

### 3.1 Art（画风）

| Art | 视觉特征 | 适用内容 |
|-----|---------|---------|
| `ligne-claire` | 均匀线条、平涂色、欧洲漫画（丁丁历险记） | 教育、平衡叙事、传记、历史 |
| `manga` | 日式漫画、动态线条、表情丰富 | 动作、情感、青少年、流行文化 |
| `realistic` | 写实比例、细节丰富 | 严肃传记、历史、人类故事 |
| `ink-brush` | 水墨笔触、东方美学 | 武侠、哲学、文化、艺术 |
| `chalk` | 粉笔质感、教育感 | 教学、解释、课堂风格 |
| `minimalist` | 极简线条、留白多 | 概念、哲学、简洁叙事 |

### 3.2 Tone（基调）

| Tone | 氛围特征 | 最佳搭配 Art |
|------|---------|-------------|
| `neutral` | 客观、平衡 | ligne-claire, manga |
| `warm` | 怀旧、温暖、个人化 | ligne-claire, manga, realistic |
| `dramatic` | 高对比、紧张、戏剧性 | manga, realistic |
| `romantic` | 柔和、装饰、情感 | manga（shoujo） |
| `energetic` | 动感、活力、快速 | manga（action/shounen） |
| `vintage` | 复古、做旧、怀旧 | ligne-claire, realistic |
| `action` | 战斗、动态、冲击 | manga, ink-brush（wuxia） |

### 3.3 Preset（预设组合）

| Preset | Art + Tone + 特殊规则 | 适用内容 |
|--------|---------------------|---------|
| `ohmsha` | manga + neutral | 视觉隐喻、无对话头像、小工具揭示 |
| `wuxia` | ink-brush + action | 气效、战斗视觉、氛围感 |
| `shoujo` | manga + romantic | 装饰元素、眼睛细节、浪漫节拍 |
| `concept-story` | manga + warm | 视觉符号系统、成长弧、对话+动作平衡 |
| `four-panel` | minimalist + neutral + four-panel layout | 起承转合、黑白+ spot color、火柴人 |

### 3.4 Layout（面板布局）

| Layout | 适用场景 |
|--------|---------|
| `standard` | 常规多面板 |
| `cinematic` | 电影感宽面板 |
| `dense` | 密集信息面板 |
| `splash` | 单大画面 |
| `mixed` | 混合大小面板 |
| `webtoon` | 竖屏滚动条漫 |
| `four-panel` | 四格漫画 |

---

## 四、baoyu-infographic 风格库

### 4.1 Layout（21 种信息结构）

| Layout | 适用内容 |
|--------|---------|
| `linear-progression` | 时间线、流程、教程 |
| `binary-comparison` | A vs B、前后、利弊 |
| `comparison-matrix` | 多因素对比 |
| `hierarchical-layers` | 金字塔、优先级 |
| `tree-branching` | 分类、分类学 |
| `hub-spoke` | 中心概念+关联项 |
| `structural-breakdown` | 爆炸图、剖面图 |
| `bento-grid` | 多主题概览（默认） |
| `iceberg` | 表面 vs 隐藏 |
| `bridge` | 问题-解决方案 |
| `funnel` | 转化、过滤 |
| `isometric-map` | 空间关系 |
| `dashboard` | 指标、KPI |
| `periodic-table` | 分类集合 |
| `comic-strip` | 叙事、序列 |
| `story-mountain` | 情节结构、张力弧 |
| `jigsaw` | 互联部分 |
| `venn-diagram` | 重叠概念 |
| `winding-roadmap` | 旅程、里程碑 |
| `circular-flow` | 循环、重复流程 |
| `dense-modules` | 高密度模块、数据丰富指南 |

### 4.2 Style（21 种渲染风格）

| Style | 视觉特征 |
|-------|---------|
| `craft-handmade` | 手绘、纸工艺（默认） |
| `claymation` | 3D 黏土、定格动画 |
| `kawaii` | 日式可爱、粉彩 |
| `storybook-watercolor` | 柔和水彩、异想天开 |
| `chalkboard` | 黑板粉笔 |
| `cyberpunk-neon` | 霓虹发光、未来感 |
| `bold-graphic` | 漫画风、半调 |
| `aged-academia` | 复古科学、棕褐 |
| `corporate-memphis` | 扁平矢量、鲜艳 |
| `technical-schematic` | 蓝图、工程 |
| `origami` | 折纸、几何 |
| `pixel-art` | 复古 8-bit |
| `ui-wireframe` | 灰度界面原型 |
| `subway-map` | 地铁图 |
| `ikea-manual` | 极简线条 |
| `knolling` | 整理平铺 |
| `lego-brick` | 乐高积木 |
| `pop-laboratory` | 蓝图网格、坐标标记、实验室精度 |
| `morandi-journal` | 手绘涂鸦、暖莫兰迪色调 |
| `retro-pop-grid` | 70 年代复古波普、瑞士网格、粗轮廓 |
| `hand-drawn-edu` | 马卡龙粉彩、手绘摇摆、火柴人 |

### 4.3 推荐组合

| 内容类型 | Layout + Style |
|---------|----------------|
| 时间线/历史 | `linear-progression` + `craft-handmade` |
| 步骤教程 | `linear-progression` + `ikea-manual` |
| A vs B | `binary-comparison` + `corporate-memphis` |
| 层级 | `hierarchical-layers` + `craft-handmade` |
| 重叠 | `venn-diagram` + `craft-handmade` |
| 转化 | `funnel` + `corporate-memphis` |
| 循环 | `circular-flow` + `craft-handmade` |
| 技术 | `structural-breakdown` + `technical-schematic` |
| 指标 | `dashboard` + `corporate-memphis` |
| 教育 | `bento-grid` + `chalkboard` |
| 旅程 | `winding-roadmap` + `storybook-watercolor` |
| 分类 | `periodic-table` + `bold-graphic` |
| 产品指南 | `dense-modules` + `morandi-journal` |
| 技术指南 | `dense-modules` + `pop-laboratory` |
| 潮流指南 | `dense-modules` + `retro-pop-grid` |
| 教育图表 | `hub-spoke` + `hand-drawn-edu` |
| 流程教程 | `linear-progression` + `hand-drawn-edu` |

---

## 五、公众号配图自动匹配规则

### 5.1 配图数量硬规则

| 正文字数 | 配图数 |
|---------|-------|
| < 2500 字 | 0–1 张 |
| ≥ 2500 字 | 0–2 张 |

**数量永远可以是 0。** 不要为了"长文必须配图"凑数。

### 5.2 四类触发条件（满足任一才插图）

1. **数据 / 数字** → 一个核心数字比一段文字更震撼
2. **对比** → A vs B 的并列结构
3. **流程 / 演化** → 有时间或步骤的走向
4. **结构关系** → 文字说不清的拓扑或分层

### 5.3 禁止插图场景

- ⛔ 纯观点段落
- ⛔ 单一概念定义
- ⛔ 列表已经能说清的
- ⛔ "为了让文章看起来更专业"

### 5.4 内容类型 → 风格匹配表

| 文章内容信号 | 推荐 Skill | 推荐 Type/Layout | 推荐 Style/Preset |
|-------------|-----------|-----------------|------------------|
| API、指标、数据、技术深度 | article-illustrator | infographic | blueprint（tech-explainer） |
| 概念解释、教程、how-to | article-illustrator | infographic | vector-illustration（knowledge-base） |
| 产品指南、SaaS 文档 | article-illustrator | infographic | notion（saas-guide） |
| 步骤流程、工作流 | article-illustrator | flowchart | vector-illustration（tutorial） |
| 架构、系统关系 | article-illustrator | framework | blueprint（system-design） |
| A vs B、前后对比 | article-illustrator | comparison | vector-illustration（versus）或 ink-notes（ink-notes-compare） |
| 个人故事、成长、反思 | article-illustrator | scene | warm（storytelling） |
| 历史、演化、里程碑 | article-illustrator | timeline | elegant（history）或 warm（evolution） |
| 观点、评论、文化 | article-illustrator | scene | screen-print（opinion-piece/cinematic） |
| 数据新闻、指标报告 | article-illustrator | infographic | editorial（data-report） |
| 叙事、场景、情绪、传记 | comic | 按情节选 layout | ligne-claire + warm/neutral 或 manga + dramatic |
| 武侠、动作、东方美学 | comic | cinematic/splash | ink-brush + action（wuxia） |
| 四格漫画、轻叙事 | comic | four-panel | minimalist + neutral（four-panel） |
| 高密度信息总结、数据可视化 | infographic | 按数据结构选 layout | 按调性选 style（默认 bento-grid + craft-handmade） |
| 多主题概览 | infographic | bento-grid | craft-handmade 或 morandi-journal |
| 分类集合 | infographic | periodic-table | bold-graphic |
| 旅程、里程碑 | infographic | winding-roadmap | storybook-watercolor |
| 循环流程 | infographic | circular-flow | craft-handmade |
| 问题-解决方案 | infographic | bridge | corporate-memphis |
| 表面 vs 隐藏 | infographic | iceberg | craft-handmade |

### 5.5 中文字硬规则

Agnes 模型对中文极不稳定。**提示词中最多出现 1-2 个中文主题词**（如"百亿补贴"），其余信息用英文关键词、画面元素、表情、构图表达。不要在提示词里要求多行中文说明、对话框、标签文字。如需精确中文文字，用 Python/PIL 后期叠加。

### 5.6 默认尺寸

- 正文图默认 **1024x576**（16:9 宽图），适合公众号正文嵌入
- 竖图场景用 **576x1024**

### 5.7 独立配图

双账号各自生成各自的配图，根据文章内容自动选择合适风格。

---

## 六、Agnes API 调用规范

```bash
RESPONSE=$(curl -sSL --max-time 420 --noproxy '*' \
  -X POST "https://apihub.agnes-ai.com/v1/images/generations" \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "<构造好的 prompt>",
    "size": "1024x576",
    "n": 1
  }')
URL=$(echo $RESPONSE | jq -r '.data[0].url')
curl -sSL --max-time 60 --noproxy '*' "$URL" -o /absolute/path/to/body-image.png
```

**关键注意：**
- 必须加 `--noproxy '*'` 绕过系统代理
- 超时 420 秒
- 下载失败重试一次
- `--out` 必须用绝对路径
