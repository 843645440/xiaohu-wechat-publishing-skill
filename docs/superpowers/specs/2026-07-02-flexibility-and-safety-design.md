# 公众号 Skill 灵活性入口 + 安全加固设计

> 日期:2026-07-02
> 范围:`xiaohu-wechat-publishing` skill(指令层为主 + 轻量代码包装)
> 前置:`docs/superpowers/specs/2026-06-21-wechat-anti-lowquality-design.md`(已落地)
> 目标:让 skill 在不同使用强度(只排版 / 排版配图 / 全流程 / cron)下都安全可用,移除可绕过的安全开关,补齐针对性回归测试,**改动不破坏现有发布管线**。

---

## 0. 名词与背景(供外部 Agent 审阅)

- **Skill**:`xiaohu-wechat-publishing`,公众号写作/排版/配图/发布的规则 + 脚本,`SKILL.md` 是运行契约。
- **publish_pipe.py**:发布主入口,排版 → 图位注入 → 硬校验(`validate_publish_ready`)→ 草稿箱。
- **AI 守卫**:`publish_history.check_ai_disclosure()`,正则黑名单扫描,命中即拒发(用户最高优先级规则:严禁出现 AI 身份披露)。
- **当前问题**:
  1. AI 守卫有 `--skip-ai-guard` flag 和 `HERMES_WECHAT_SKIP_AI_GUARD` 环境变量,一行就能关掉"最高优先级"规则。
  2. SKILL.md 把流程写成一条龙,agent 倾向每次从头走到发布,即使用户只要排版。
  3. 高风险关键词硬编码在 `publish_history.py`,文档又抄一份,两处靠人工同步。
  4. `format.py` 1824 行,核心正则(AI 守卫)和排版元素无测试,改动后无法快速验证。

---

## 1. 用户决策(澄清会话结果)

| 维度 | 决策 |
|---|---|
| 灵活性层次 | **指令层为主 + 轻量代码包装**(方案 B),不重构核心管线 |
| AI 守卫开关 | **完全移除** `--skip-ai-guard` 和 env var |
| 测试保障 | **加针对性回归测试**(AI 正则、风险词、纯函数、注入) |
| 风险关键词 | **抽到独立数据文件** `data/high-risk-keywords.json` |
| format 解耦范围 | **只抽 4 个最简纯函数**,CJK/样式/高亮逻辑不动 |

**核心约束**:每一步改动对现有发布管线是加性的或纯删除(删开关),不重构主流程逻辑,确保"改动后仍可用"。

---

## 2. 改造 1:AI 守卫——移除绕过开关(安全)

**现状**:`publish_pipe.py:474-487` 的 `--skip-ai-guard` + `HERMES_WECHAT_SKIP_AI_GUARD`,一行即可关掉 AI 披露扫描。

**改动**:

### 2.1 `scripts/publish_pipe.py`
- 删除 `--skip-ai-guard` 参数定义(L474-475)。
- `_run_pipe()` 中 AI 检查改为**无条件执行**:删除 L484-487 的 `if not args.skip_ai_guard and not os.environ.get(...)` 分支,直接调 `check_ai_disclosure(md_text, raise_on_hit=True)`。
- 检查时机不变:`--input` 模式下、排版前、读 md 之后立即扫。

### 2.2 `scripts/publish_history.py`
- `check_ai_disclosure()` 命中时的错误提示(L57-60)删除"可设置环境变量跳过"那句,改为:"请删除上述内容后再发布。AI 披露扫描为发布前硬门禁,不可跳过。"

### 2.3 `prompts/writing-persona.md`
- L87 "不要尝试 `--skip-ai-guard` 绕过"删除(flag 不复存在)。
- 改为:"AI 披露扫描是发布前硬门禁,**不可跳过**。若误加了 AI 声明,必须删除后再发。"

### 2.4 行为变化与边界
- `--input` 模式:AI 扫描变成不可关闭的硬门。
- `--dir` 模式(跳过排版发已有 HTML):**原本就不扫**(不读 md),保持不变——属对已成型 HTML 的信任操作;如需扫描,可用 `publish_history.py --check-file <html>` 单独扫。
- **trade-off**:若未来某篇稿因合规要求**必须**带 AI 声明(如客户/平台要求),需临时改代码。考虑到账号定位是"绝不暴露 AI 身份",可接受。

---

## 3. 改造 2:灵活性——纯指令层入口识别(无代码改动)

**核心**:代码层零改动,只改 SKILL.md,教 agent 用现有 `--dry-run` / `--dir` / 全流程准确匹配用户的 4+1 种使用强度。

### 3.1 SKILL.md 新增"入口与停步"章节

位置:现有"任务路由"(L58-65)之后,取代其模糊表述。

**入口模式表**:

| 用户场景 | 典型说法 | agent 行为 | 代码命令 |
|---|---|---|---|
| 只排版 | "排版这篇"/"format 一下"/"微信排版" | 排版+注入+本地校验,**停在产物** | `publish_pipe.py --input X.md --cover C.png --dry-run` |
| 排版+配图但不发 | "做完整版给我看"/"排版配图" | 同上,**停在产物,明确告知"未发布"** | 同上 `--dry-run` |
| 全流程发布 | "推草稿箱"/"发公众号"/"直接发" | dry-run 通过后正式推 | dry-run → 去掉 `--dry-run` |
| 跳过排版发已有稿 | "这篇排好了直接发" | 信任已有 HTML | `publish_pipe.py --dir <目录> --cover C.png --account X` |
| 只写作 | 用户只给主题/素材 | 写完停下,**问"只排版还是发?"**,不自动继续 | 写作 + 等确认 |

### 3.2 三条停步硬原则(写进 SKILL.md)

1. **默认停步**:除非用户明确说出"发/推草稿箱/直接发/发布"等动词,否则 agent 完成被要求的步骤后**必须停下**,展示产物路径,问"要不要进入下一步"。
2. **dry-run 不是发布**:`--dry-run` 产物不能视为已发布。agent 完成后必须报告"已排版/已配图,**未发布**",严禁说"发布成功"。
3. **多步请求按序停步**:用户说"写完排版配图",agent 做完这三步后停在发布前,即使没说"先停"。

### 3.3 修订现有"任务路由"原文

- 保留"写作 → 配图 → 排版 → 发布"的顺序。
- **删除自动延续到发布**:改为"走到发布前必须确认"。

---

## 4. 改造 3:高风险关键词抽到独立数据文件

**现状**:`publish_history.py:67-74` 硬编码 `HIGH_RISK_KEYWORDS`;`quality-and-risk.md:73-77` 抄了一份。两处漂移风险。

### 4.1 新建 `data/high-risk-keywords.json`

```json
{
  "version": "1.0",
  "note": "命中即 warning(不阻断)。改这里即可,无需改代码或文档。来源:quality-and-risk.md C 节。",
  "keywords": [
    {"word": "降息"}, {"word": "加息"}, {"word": "降准"},
    {"word": "货币政策"}, {"word": "财政政策"}, {"word": "监管收紧"},
    {"word": "政策转向"}, {"word": "政策信号"}, {"word": "救市"},
    {"word": "抄底"}, {"word": "牛市"}, {"word": "熊市"},
    {"word": "涨停"}, {"word": "跌停"}, {"word": "暴跌"},
    {"word": "大盘", "note": "易误报:大盘鸡/大盘股(合法)。warning 级,人工判断"},
    {"word": "唱多"}, {"word": "唱空"}, {"word": "买入"}, {"word": "卖出"},
    {"word": "点位"}, {"word": "目标价"},
    {"word": "地缘"}, {"word": "制裁"}, {"word": "站队"}, {"word": "脱钩"},
    {"word": "领导人"}, {"word": "群体事件"}, {"word": "维权"}, {"word": "罢工"},
    {"word": "维稳"}, {"word": "对立"}
  ]
}
```

支持两种元素格式:纯字符串 `"降息"` 或对象 `{"word": "大盘", "note": "..."}`(向后兼容,note 可选)。

### 4.2 `scripts/publish_history.py` 改造

- 删除硬编码 `HIGH_RISK_KEYWORDS` 常量(L67-74)。
- 新增 `_load_high_risk_keywords()`:
  - 读 `data/high-risk-keywords.json`(相对 SKILL_DIR)。
  - 解析:列表元素为字符串→直接用;为对象→取 `word`,保留 `note`。
  - **文件缺失/损坏时回退**到内置最小集(`["降息", "加息", "抄底", "牛市", "熊市", "地缘", "制裁", "领导人"]`)+ 打印 warning,保证不因文件丢失而失效。
- `check_high_risk()` 改为接收 `keywords` 参数(已是当前签名,默认值改为 None→内部调 `_load_high_risk_keywords()`)。
- 返回的命中元组从 `(line_no, keyword, snippet)` 扩展为 `(line_no, keyword, snippet, note_or_empty)`,打印时附带 note。

### 4.3 `prompts/quality-and-risk.md` 改造

- C 节关键词清单(L73-77)删除,改为:"高风险关键词清单见 `data/high-risk-keywords.json`(命中即 warning)。调整词表无需改代码或本文档。"

---

## 5. 改造 4:format.py 最小解耦 + 针对性回归测试

### 5.1 抽 4 个最简纯函数到 `scripts/format_utils.py`

| 函数(format.py 原行号) | 说明 |
|---|---|
| `count_words` (L202-208) | 中英字数统计 |
| `extract_title` (L211-227) | frontmatter / H1 / 文件名三路提取 |
| `strip_frontmatter` (L230-232) | 剥 YAML frontmatter |
| `_hex_to_rgb` (L886-889) | `#RRGGBB → (r,g,b)`,抽出去掉下划线前缀,改名 `hex_to_rgb` |

**`format.py` 改动**:顶部加 `from format_utils import (count_words, extract_title, strip_frontmatter, hex_to_rgb)`,删除这 4 个函数体。**其余 1800+ 行渲染逻辑一行不动。**

**不抽出**(逻辑复杂、易回归):`fix_cjk_spacing`、`fix_cjk_bold_punctuation`、`_basic_syntax_highlight`、`inject_inline_styles`、所有容器/列表/callout 转换。CJK 等函数的测试直接 import format.py 测,不依赖物理位置。

**风险控制**:抽出的函数名不变,调用处代码零修改;纯函数无副作用,物理位置改变不影响行为。

### 5.2 新增 4 个测试文件(unittest,与现有一致)

| 测试文件 | 覆盖 | 关键用例 |
|---|---|---|
| `tests/test_ai_disclosure.py` | `check_ai_disclosure` | 7 种 AI 披露模式各命中 1 例;**反例(不误报)**:"这家公司叫 OpenAI"、"用 GPT 举个例子"、"人工智能领域"、正常财经句 |
| `tests/test_high_risk_scan.py` | `check_high_risk` + JSON 加载 | 各关键词命中;JSON 缺失回退最小集;note 正确输出 |
| `tests/test_format_utils.py` | 4 个纯函数 | 字数(纯中/纯英/混合);标题三种来源;frontmatter 剥离;hex→rgb(含 `#fff` 短格式) |
| `tests/test_image_injector.py` | `inject` / `inject_markers` / `resolve_image` | marker 解析/未解析保留/按位置插入/extra_files 预复制/路径查找 |

**额外**:CJK 函数测试写进 `test_format_utils.py` 但 import 自 `format`(`fix_cjk_spacing` 等),覆盖中英、中数空格、跳过代码块/URL、标点移出加粗。

**现有测试**:`test_publish_validation.py`、`test_run_script.py` 保持原样,确保旧测试继续过。

---

## 6. 文档同步(收尾)

| 文件 | 改动 |
|---|---|
| `SKILL.md` | "任务路由"→"入口与停步"章节(第 3 节);"发布前硬校验"补充 AI 扫描不可关闭;"先读什么"补 `data/high-risk-keywords.json` |
| `AGENTS.md` / `CLAUDE.md` | 移除 `--skip-ai-guard` 提及;关键词文件路径;硬门禁描述 |
| `prompts/quality-and-risk.md` | C 节关键词清单 → 指向 JSON 文件 |
| `prompts/writing-persona.md` | L87 改为"AI 扫描不可跳过" |

---

## 7. 交付物清单

| 文件 | 动作 |
|---|---|
| `scripts/publish_pipe.py` | 删 `--skip-ai-guard` 参数与分支 |
| `scripts/publish_history.py` | 删 env var 提示;关键词改读 JSON + 回退 |
| `scripts/format.py` | 抽 4 函数,加 import |
| `scripts/format_utils.py` | **新增**(4 个纯函数) |
| `data/high-risk-keywords.json` | **新增** |
| `prompts/quality-and-risk.md` | C 节关键词 → 指向 JSON |
| `prompts/writing-persona.md` | L87 改写 |
| `SKILL.md` | 新增"入口与停步"章节;更新硬校验/先读什么 |
| `AGENTS.md` / `CLAUDE.md` | 同步上述变化 |
| `tests/test_ai_disclosure.py` | **新增** |
| `tests/test_high_risk_scan.py` | **新增** |
| `tests/test_format_utils.py` | **新增** |
| `tests/test_image_injector.py` | **新增** |

---

## 8. 验证方式

1. **现有测试全过**:`python3 -m unittest discover -s tests`。
2. **新测试全过**:4 个新测试文件,含正例(命中)与反例(不误报)。
3. **AI 守卫回归**:手工造一篇含 AI 披露的 md,确认 `publish_pipe.py --input ... --dry-run` 在**任何参数下**都拒发(无法 `--skip-ai-guard`)。
4. **关键词加载回归**:删除 JSON 文件,确认回退到最小集 + warning;恢复后确认正常加载。
5. **format 解耦回归**:用一篇真实文章跑 `format.py`,与改动前产物 diff 应为空(渲染输出不变)。
6. **指令层验证**:模拟"只排版"场景,确认 agent 用 `--dry-run` 并停在产物,不自走发布。

---

## 9. 非目标(本次不做)

- **不重构 `format.py` 主体**:容器/样式/列表/callout 转换逻辑不动(YAGNI + 回归风险)。
- **不加 SSRF 防护**:`replace_all_images` 的外部图片下载,在"只有自己写文章"场景风险低,以后单独立项。
- **不拆 `publish_pipe.py`**:它是核心主入口,拆分回归风险最高,违背"别改坏"诉求。
- **不改配图体系**:baoyu 风格、双账号共享图、digest 截断逻辑,本次不动。
- **不引入新依赖**:JSON 用标准库,测试用 unittest,不引 pyyaml/pytest。

---

## 10. 实施顺序建议(供 writing-plans 参考)

按回归风险从低到高,每步可独立验证:

1. **数据文件**(改造 3 的 4.1):新建 `data/high-risk-keywords.json`,不影响任何现有代码。
2. **测试**(改造 4 的 5.2):新测试先写,**在改代码前跑一遍**——AI 守卫/关键词测试此时应部分通过(验证现有行为),作为改动前的基线。
3. **关键词加载**(改造 3 的 4.2):改 `publish_history.py`,跑测试。
4. **AI 守卫**(改造 2):删 flag,跑测试 + 手工 dry-run 验证拒发。
5. **format 解耦**(改造 4 的 5.1):抽 4 函数,跑测试 + 真实文章 diff。
6. **指令层 + 文档**(改造 2 的 3.x + 第 6 节):改 SKILL.md / prompts / AGENTS.md,无需跑代码测试。
