# 轻量视觉生成流程

> 每篇文章都进入视觉阶段。封面必做；正文图按文章内容决定 0-2 张。不要加载完整风格库，不要为了“专业感”硬凑图。

## 产物

Job 目录至少包含：

```text
cover.png
visual-meta.json
body-1.png / body-2.png  # 如有正文图
```

## 封面

- 封面必须生成，保持账号品牌气质。
- 封面标题尽量短，不把正文结论写死。
- 封面失败时可以跳过封面参数推草稿箱，但报告里说明“封面失败，需后台手动补封面”。

可继续使用现有渲染脚本或 Agnes 生图。Swiss/Editorial 旧流程不用展开到主上下文里。

## 正文图判断

先判断是否需要正文图：

- 数据、指标、趋势：适合 1 张信息图。
- 平台规则、消费、职场、生活场景：适合 1 张场景图。
- A/B 对比、前后变化、两个方案：适合 1 张对比图。
- 工具流程、产业链、工作流：适合 1 张流程/结构图。
- 纯观点、短列表、简单解释：正文图为 0。

默认 0-1 张，信息密度高才 2 张。

## 四条轻量路径

### 1. 信息图

用于数据、指标、趋势、排行榜、成本变化。

Prompt 要点：

```text
TYPE: infographic
SUBJECT: article-specific topic
DATA POINTS: 2-4 concise facts
STYLE: clean editorial infographic, clear hierarchy
TEXT: max 1-2 short Chinese keywords
NEGATIVE: no dense Chinese text, no fake dashboard, no watermark
SIZE: 1024x576
```

### 2. 场景图

用于平台规则、消费、职场、小店、家庭、普通用户。

Prompt 要点：

```text
TYPE: editorial scene
SUBJECT: concrete scene from article
CHARACTERS: 1-3 ordinary people
MOOD: realistic, restrained, not sensational
STYLE: warm editorial illustration
TEXT: no text or max 1 short Chinese keyword
SIZE: 1024x576
```

### 3. 对比图

用于前后变化、A/B、两个平台、两种方案。

Prompt 要点：

```text
TYPE: comparison visual
LEFT: old state or option A
RIGHT: new state or option B
STYLE: clean split composition
TEXT: max 1-2 short labels
NEGATIVE: no dense Chinese text, no logos, no watermark
SIZE: 1024x576
```

### 4. 流程/结构图

用于产业链、工作流、工具链、平台规则流转。

Prompt 要点：

```text
TYPE: flow / structure map
NODES: 3-5 article-specific nodes
RELATION: arrows, layers, or simple map
STYLE: blueprint or clean editorial diagram
TEXT: max 1-2 short Chinese keywords
SIZE: 1024x576
```

## visual-meta.json

生成前写入本次视觉意图，方便人工复盘。它不再作为长期防重历史。

```json
{
  "cover": {
    "type": "editorial-cover",
    "subject": "文章具体主题",
    "prompt_key": "account-date-topic-cover"
  },
  "body_images": [
    {
      "file": "body-1.png",
      "type": "infographic | scene | comparison | flow",
      "subject": "图片服务的具体段落观点",
      "prompt_key": "account-date-topic-body-1"
    }
  ]
}
```

## Agnes API

```bash
RESPONSE=$(curl -sSL --max-time 420 --noproxy '*' \
  -X POST "https://apihub.agnes-ai.com/v1/images/generations" \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "<structured prompt>",
    "size": "1024x576",
    "n": 1
  }')

URL=$(printf "%s" "$RESPONSE" | jq -r ".data[0].url")
curl -sSL --max-time 60 --noproxy "*" "$URL" -o /absolute/path/body-1.png
```

规则：

- 模型固定 `agnes-image-2.1-flash`。
- 所有路径用绝对路径。
- 中文最多 1-2 个短词，其余用英文视觉描述。
- 下载失败重试一次。

## 失败容错

- 封面失败：跳过 `--cover` 或后台手动补封面，报告说明。
- 正文图失败：删除对应 `<!-- img:... -->` marker，不传该图，报告说明。
- 不要因为正文图失败中断整篇文章发布。
