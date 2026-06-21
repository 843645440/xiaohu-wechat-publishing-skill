# Agnes API 正文图生成参考

## 正确的 API 端点

```
POST https://apihub.agnes-ai.com/v1/images/generations
```

**⚠️ 不要用 `https://api.agnes-ai.com`，会返回 `{"code":"000201","message":"route not found"}`。**

## 请求格式

```bash
curl -X POST https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "...",
    "size": "1024x1024",
    "n": 1
  }'
```

## 响应格式

```json
{
  "created": 1781178895,
  "data": [{"url": "https://platform-outputs.agnes-ai.space/images/text-to-image/2026/06/...png"}]
}
```

下载：
```bash
curl -sSL --max-time 60 "<url>" -o output.png
```

## 环境变量

`AGNES_API_KEY` 存在 `~/.hermes/.env` 中。

## 提示词质量差异

简单提示词（如"画一张商业插画风格的图"）生成的图片效果"廉价"，缺乏设计感。

使用结构化提示词（baoyu-article-illustrator 方法）效果明显更好：
- **Type**：infographic / scene / flowchart / comparison / framework / timeline
- **Style**：editorial / minimal / watercolor / warm / notion / blueprint / elegant
- **Palette**：macaron / warm / neon / default

结构化提示词包含：ZONES（布局）、LABELS（标注数据）、COLORS（配色方案）、STYLE（风格描述）、ASPECT（构图比例）。

## 双账号正文图设计原则

同一个选题给两个账号写不同风格正文图：

| 账号 | 风格 | 正文图定位 |
|------|------|-----------|
| xiaocong / 熵增时刻 | 解释型、信息密度高 | infographic / comparison / framework |
| yeluzi / 思想的野路子 | 情绪型、讽刺感 | scene（带讽刺元素） |

## Python 批量生成模板

```python
import requests, json, os
from pathlib import Path

API_KEY = os.environ.get('AGNES_API_KEY')
API_URL = "https://apihub.agnes-ai.com/v1/images/generations"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate(prompt, filename):
    payload = {"model": "agnes-image-2.0-flash", "prompt": prompt, "size": "1024x1024", "n": 1}
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=420)
    result = resp.json()
    if resp.status_code == 200 and "data" in result:
        img_url = result["data"][0]["url"]
        img_resp = requests.get(img_url, timeout=120)
        out_path = Path(f"/tmp/{filename}")
        out_path.write_bytes(img_resp.content)
        print(f"✅ {filename}: {out_path}")
    else:
        print(f"❌ {filename}: {resp.status_code} - {result}")
```
