# 端到端发布管线命令速查（2026-05 实测通过）

本文档记录一次成功的双账号端到端发布所用的完整命令序列，供未来会话直接复用。

## 环境变量

```bash
PY="/home/ubuntu/.hermes/hermes-agent/venv/bin/python3"
SCRIPTS="/home/ubuntu/.hermes/skills/xiaohu-wechat-publishing/scripts"
```

## 1. 写稿

写入 Markdown 文件，首行必须是 `# 标题`（format.py 依赖它）。
在需要插图的位置插入 `<!-- img:filename.png -->` 标记（但注意：该标记最终位置可能漂移，后续需手动校正）。

## 2. 生成封面

```bash
$PY $SCRIPTS/render_editorial_cover.py \
  --account-style xiaocong \
  --meta-left "熵增时刻" \
  --meta-right-line1 "半导体 · 产业洞察" \
  --meta-right-line2 "2026年5月" \
  --title-line1 "半导体这轮超级周期" \
  --title-line2 "已经不是泡沫那么简单了" \
  --kicker-text "3.8万亿美元 · 六周 · 全产业链" \
  --pill-1 "SK海力士" --pill-2 "三星" --pill-3 "美光" \
  --pill-4 "8300亿资本开支" --pill-5 "AI基建" \
  --impact-top "市值增量" --impact-main "3.8万亿" --impact-sub "美元 · 6周" \
  --out /home/ubuntu/xc_cover.png
```

参数说明：
- `--account-style`: `xiaocong`（熵增）或 `yeluzi`（野路子）
- 模板自动根据 account-style 切换配色/字体差异
- 输出固定 900x383 viewport, 2x DPR → 实际 1800x766px

## 3. 生成正文图（hero 模式示例）

```bash
$PY $SCRIPTS/render_editorial_body_modular.py \
  --mode hero \
  --eyebrow "熵增时刻 · 数据冲击" \
  --title "3.8万亿美元" \
  --subtitle "标普500半导体成分股 · 6周市值增量" \
  --footer-note "数据来源：TrendForce / Bloomberg" \
  --metric-label "全球九大云服务商资本开支" \
  --metric-value "8300" --metric-unit "亿美元" --metric-note "2026年预测值" \
  --tag-1-head "韩国双雄" --tag-1-title "SK海力士 + 三星" \
  --tag-1-desc "2026Q1海力士单季利润37.6万亿韩元，同比+405%" \
  --tag-2-head "内存重估" --tag-2-title "美光科技" \
  --tag-2-desc "从周期底部到AI耗材，估值逻辑彻底切换" \
  --quote-text "需求是真的，钱也是真的，产能却是慢的。" \
  --out /home/ubuntu/xc_hero.png
```

三种模式：hero（数据冲击）、people（人物卡）、structure（结构判断）

## 4. 排版

```bash
$PY $SCRIPTS/format.py --input /home/ubuntu/tmp_xc.md --output /home/ubuntu/tmp_xc.html --format wechat
```

输出结构：
- `/home/ubuntu/tmp_xc.html/tmp_xc/article.html` ← 实际排版内容
- `/home/ubuntu/tmp_xc.html/tmp_xc/preview.html` ← 壳模板（无用）
- `/home/ubuntu/tmp_xc.html/tmp_xc/images/` ← 图片目录

## 5. 注入正文图

**方式A（自动注入，可能把图放到文末）：**
```bash
$PY $SCRIPTS/inject_body_images.py --html <article.html路径> --images <图片> --mode marker
```

**方式B（推荐：手动定位插入）：**
```python
# 读取 article.html，grep 定位目标文本，在对应 </p> 后插入
img_tag = '<section style="text-align:center;margin:24px 0 16px;"><img src="images/xc_hero.png" style="width:100%;border-radius:6px;display:block;" /></section>'
```

注入后需把图片文件 cp 到 article.html 同级的 images/ 目录：
```bash
cp /home/ubuntu/xc_hero.png /home/ubuntu/tmp_xc.html/tmp_xc/images/
```

## 6. 发布

```bash
# 清理旧 token（可选，--account 模式会自动刷新）
rm -f /tmp/wechat_token_*.json

# 熵增时刻
$PY $SCRIPTS/publish.py \
  --dir /home/ubuntu/tmp_xc.html/tmp_xc \
  --cover /home/ubuntu/xc_cover.png \
  --account xiaocong

# 野路子
$PY $SCRIPTS/publish.py \
  --dir /home/ubuntu/tmp_yl.html/tmp_yl \
  --cover /home/ubuntu/yl_cover.png \
  --account yeluzi
```

`--dir` 指向 format.py 输出子目录（含 article.html 的那个目录）。
`--cover` 路径可以是任意绝对路径，脚本会自行上传。

## 耗时参考

| 步骤 | 耗时 |
|------|------|
| 封面 x2 | ~3s |
| 正文图 x2 | ~4s |
| 排版 x2 | ~1s |
| 注入 | ~1s |
| 发布 x2 | ~20s |
| **总计** | **~30s**（不含写稿） |
