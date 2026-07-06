#!/usr/bin/env python3
"""Publish history archive and persona safety guard.

Functions:
    record_publish(...)      → append jsonl line to ~/.hermes/workspaces/wechat/publish-history.jsonl
    list_history(limit=20)   → most recent N entries
    check_ai_disclosure(text, *, raise_on_hit=True) → returns list of (line_no, snippet);
        by default raises SystemExit(2) when any pattern matches.
    build_content_signature(...) → structure/title/cover signature for anti-low-quality checks.
    check_low_quality_similarity(...) → warning-only same-account recent similarity scan.

User-level invariant (from user profile memory):
  公众号文章严禁出现"本文由AI协助撰写"之类的AI身份披露/利益相关声明.
"""

from __future__ import annotations

import json
import hashlib
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

from workspace import ensure_workspace, workspace_root


# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
HIGH_RISK_KEYWORDS_PATH = SKILL_DIR / "data" / "high-risk-keywords.json"

# 文件缺失/损坏时的内置最小回退集，保证扫描不会因数据文件丢失而失效。
_HIGH_RISK_FALLBACK = [
    "降息", "加息", "抄底", "牛市", "熊市",
    "地缘", "制裁", "领导人",
]


def _load_high_risk_keywords() -> tuple[list[str], dict[str, str]]:
    """从 data/high-risk-keywords.json 加载关键词。

    JSON 支持两种元素格式：纯字符串 "降息"，或对象 {"word": "...", "note": "..."}。
    返回 (keywords, notes)：keywords 是词列表，notes 是 word→note 的映射。
    文件缺失、损坏、格式不对（非 dict、脏数据）时一律回退到 _HIGH_RISK_FALLBACK 并打印 warning，
    保证扫描永远不会因数据文件问题而崩溃。
    """
    notes: dict[str, str] = {}
    if not HIGH_RISK_KEYWORDS_PATH.exists():
        print(f"  ⚠ 高风险关键词文件不存在: {HIGH_RISK_KEYWORDS_PATH}，使用内置最小集",
              file=sys.stderr)
        return list(_HIGH_RISK_FALLBACK), notes

    keywords: list[str] = []
    try:
        data = json.loads(HIGH_RISK_KEYWORDS_PATH.read_text(encoding="utf-8"))
        # 顶层必须是 dict（含 "keywords" 列表）；合法的 list/str/number 都视为损坏
        raw_items = data.get("keywords", []) if isinstance(data, dict) else None
        if raw_items is None:
            raise ValueError("顶层不是对象或缺少 keywords 字段")
        for item in raw_items:
            if isinstance(item, str):
                keywords.append(item)
            elif isinstance(item, dict) and "word" in item:
                keywords.append(item["word"])
                if item.get("note"):
                    notes[item["word"]] = item["note"]
            # 其它格式静默跳过，避免单条脏数据让整个加载失败
    except Exception as e:
        print(f"  ⚠ 高风险关键词文件解析失败 ({e})，使用内置最小集", file=sys.stderr)
        return list(_HIGH_RISK_FALLBACK), notes

    if not keywords:
        print(f"  ⚠ 高风险关键词文件为空，使用内置最小集", file=sys.stderr)
        return list(_HIGH_RISK_FALLBACK), notes
    return keywords, notes


AI_DISCLOSURE_PATTERNS = [
    re.compile(r"本文(由|经|是).{0,8}(AI|人工智能|大模型|GPT|Claude|Hermes|机器人).{0,20}(协助|辅助|生成|撰写|创作|写作|完成|编辑|参与|润色)"),
    re.compile(r"(AI|人工智能).{0,8}(协助|辅助).{0,8}(撰写|生成|写作|创作)"),
    re.compile(r"本文.{0,10}(在|由|借助).{0,10}(Hermes|Agent|大模型|LLM)"),
    re.compile(r"利益相关[:：]"),
    re.compile(r"本.{0,3}(账号|公众号).{0,8}(由|是|为).{0,20}(AI|大模型|Agent)"),
    re.compile(r"以上内容(由|经).{0,8}(AI|大模型|机器)"),
    re.compile(r"This article was (written|generated|created|drafted) (by|with) (AI|GPT|Claude|an AI|a large language model)", re.IGNORECASE),
]


def check_ai_disclosure(text: str, *, raise_on_hit: bool = True) -> list[tuple[int, str]]:
    """Scan text for AI-disclosure phrases. Returns [(line_no, snippet)] hits.

    When raise_on_hit=True (default), prints all hits and exits with code 2
    on any match — meant to be called as a publish-time hard gate.
    """
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat in AI_DISCLOSURE_PATTERNS:
            m = pat.search(line)
            if m:
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                hits.append((i, snippet))
                break
    if hits and raise_on_hit:
        print("\n✗ 检测到 AI 身份披露 / 利益相关声明（用户硬规则禁止）：", file=sys.stderr)
        for ln, sn in hits:
            print(f"  行 {ln}: {sn}", file=sys.stderr)
        print(
            "\n  → 请删除上述内容后再发布。AI 披露扫描为发布前硬门禁，不可跳过。",
            sep="\n", file=sys.stderr,
        )
        raise SystemExit(2)
    return hits


# 高风险关键词（政治/财经/敏感）软扫描——命中只告警、不阻断。
# 规则来源：prompts/quality-and-risk.md C 节。词表从 data/high-risk-keywords.json 加载。
def check_high_risk(text: str, *, keywords=None, notes: dict[str, str] | None = None
                    ) -> list[tuple[int, str, str]]:
    """Soft-scan text for high-risk (politics/finance/sensitive) keywords.

    Warning-only — NEVER raises or blocks. Returns [(line_no, keyword, snippet)],
    deduplicated to the first occurrence of each keyword so warnings stay readable.
    When the keyword has a `note`（易误报提示），note 会以可读方式追加到 snippet 末尾，
    便于人工判断是否误报。返回值仍是三元组，向后兼容已有调用方。
    Callers should print these as warnings and ask a human to confirm the angle.
    """
    if keywords is None:
        keywords, loaded_notes = _load_high_risk_keywords()
        if notes is None:
            notes = loaded_notes
    notes = notes or {}
    seen: set[str] = set()
    hits: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for kw in keywords:
            if kw and kw in line and kw not in seen:
                seen.add(kw)
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                # 把 note 拼进 snippet（如 "大盘 <易误报: 大盘鸡>"），不改变三元组结构
                note = notes.get(kw)
                if note:
                    snippet = f"{snippet}  <易误报: {note}>"
                hits.append((i, kw, snippet))
    return hits


def print_high_risk_warnings(hits: list[tuple[int, str, str]]) -> None:
    """Pretty-print high-risk soft-scan hits to stderr (warning, non-blocking)."""
    if not hits:
        return
    print("\n⚠ 高风险关键词软扫描命中（不阻断，请人工确认是否改软切口/换题）：", file=sys.stderr)
    for ln, kw, sn in hits:
        print(f"  行 {ln} [{kw}]: {sn}", file=sys.stderr)
    print("  → 规避方式见 prompts/quality-and-risk.md C 节。\n", file=sys.stderr)


GENERIC_HEADING_PATTERNS = [
    "事实底座", "背景解释", "原创分析", "普通人影响", "中国变量", "建设性结论",
    "克制结论", "结语", "总结", "这件事意味着什么", "影响是什么", "为什么重要",
]

TITLE_PATTERN_RULES = [
    ("not_x_but_y", re.compile(r"不是.+(而是|是).+")),
    ("x_changed_y_feels", re.compile(r".+(变了|变化了).+(先|会|正在).+")),
    ("this_change_means", re.compile(r"(这次|这个|一项|一条).*(变化|新规|动作).*(说明|意味着|背后)")),
    ("question", re.compile(r"[？?]$|为什么|怎么|如何")),
    ("number_anchor", re.compile(r"\d|万|亿|%|％|倍")),
    ("contrast", re.compile(r"表面|本质|过去|现在|以前|如今|背后|真正")),
]


def _compact_sequence(items: list[str], *, limit: int = 18) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and (not out or out[-1] != item):
            out.append(item)
    return out[:limit]


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4:].lstrip()
    return text


def _plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    value = re.sub(r"\s+", "", value)
    return value.strip()


def _title_pattern(title: str) -> str:
    compact = _plain_text(title)
    for name, pattern in TITLE_PATTERN_RULES:
        if pattern.search(compact):
            return name
    if len(compact) <= 12:
        return "short_direct"
    return "direct_statement"


def _extract_md_headings(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(#{2,4})\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(2).strip(" #"))
    return headings


def _extract_html_headings(html: str) -> list[str]:
    headings = []
    for tag, value in re.findall(r"<(h[2-4])[^>]*>(.*?)</\1>", html or "", flags=re.I | re.S):
        text = _plain_text(value)
        if text:
            headings.append(text)
    return headings


def _heading_token(heading: str) -> str:
    compact = _plain_text(heading)
    for pattern in GENERIC_HEADING_PATTERNS:
        if pattern in compact:
            return f"generic:{pattern}"
    if re.search(r"[？?]$|为什么|怎么|如何", compact):
        return "question"
    if re.search(r"过去|现在|以前|如今|表面|本质|对比|不同", compact):
        return "contrast"
    if re.search(r"\d|万|亿|%|％|倍", compact):
        return "number"
    return re.sub(r"[\d０-９一二三四五六七八九十百千万亿%％]+", "#", compact)[:18]


def _element_sequence(markdown_text: str) -> list[str]:
    items: list[str] = []
    in_code = False
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("```"):
            items.append("CODE")
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^#{2,4}\s+", line):
            items.append("H")
        elif line.startswith(">"):
            items.append("QUOTE")
        elif ("<!--" in line and "img:" in line) or re.search(r"!\[[^\]]*\]\(", line):
            items.append("IMG")
        elif "|" in line and line.count("|") >= 2:
            items.append("TABLE")
        elif re.match(r"^([-*+]|\d+[.、])\s+", line):
            items.append("LIST")
        elif re.match(r"^-{3,}$", line):
            items.append("HR")
        else:
            items.append("P")
    return _compact_sequence(items)


def _opening_pattern(markdown_text: str) -> str:
    text = _strip_frontmatter(markdown_text)
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith("<!--"):
            continue
        compact = _plain_text(block)
        if not compact:
            continue
        if compact.startswith(("近日", "最近", "今天", "刚刚")):
            return "news_lead"
        if re.search(r"^\d|^[一二三四五六七八九十].*个", compact):
            return "number_lead"
        if re.search(r"[？?]$", compact[:80]) or compact.startswith(("为什么", "怎么", "如何")):
            return "question_lead"
        if re.search(r"办公室|通勤|小店|账单|订单|家庭|打工人|消费者|程序员|创作者", compact[:120]):
            return "scene_lead"
        if compact.startswith(("不是", "很多人以为", "表面看")):
            return "contrast_lead"
        return "direct_lead"
    return "unknown"


def _structure_archetype(markdown_text: str, title: str, heading_tokens: list[str], generic_count: int) -> str:
    joined = "\n".join([title, markdown_text, " ".join(heading_tokens)])
    if generic_count >= 3:
        return "fixed_quality_template"
    if heading_tokens.count("question") >= 3 or re.search(r"问答|Q&A|问题", joined, flags=re.I):
        return "qa"
    if re.search(r"时间线|节点|第[一二三四五六七八九十]阶段|20\d{2}", joined):
        return "timeline"
    if re.search(r"过去|现在|以前|如今|表面|本质|对比|不同", joined):
        return "contrast"
    if re.search(r"清单|误区|建议|步骤|做法", joined):
        return "list"
    if re.search(r"办公室|通勤|小店|账单|订单|家庭|场景", joined):
        return "scene"
    if re.search(r"\d|万|亿|%|％|倍", title):
        return "data_explainer"
    return "analysis"


def _cover_signature(cover_path: str | Path | None) -> dict:
    if not cover_path:
        return {}
    path = Path(cover_path)
    sig = {
        "file_name": path.name,
        "suffix": path.suffix.lower(),
        "exists": path.exists(),
    }
    if path.exists():
        sig["bytes"] = path.stat().st_size
        try:
            from PIL import Image
            with Image.open(path) as img:
                sig["size"] = f"{img.width}x{img.height}"
        except Exception:
            sig["size"] = "unknown"
    return sig


def _parse_visual_meta_comment(raw: str) -> dict:
    out: dict[str, str] = {}
    for part in re.split(r"[;；]\s*", raw.strip()):
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
        elif "：" in part:
            key, value = part.split("：", 1)
        elif ":" in part:
            key, value = part.split(":", 1)
        else:
            continue
        out[key.strip().lower().replace("-", "_")] = value.strip().strip('"\'')
    return out


def _visual_meta_from_comments(markdown_text: str) -> dict:
    cover: dict = {}
    body_images: list[dict] = []
    for kind, raw in re.findall(r"<!--\s*(cover-meta|image-meta)\s*:\s*(.*?)\s*-->", markdown_text or "", flags=re.I | re.S):
        item = _parse_visual_meta_comment(raw)
        if not item:
            continue
        if kind.lower() == "cover-meta":
            cover.update(item)
        else:
            body_images.append(item)
    return {"cover": cover, "body_images": body_images}


def _normalise_visual_meta(visual_meta: dict | None, markdown_text: str) -> dict:
    meta = visual_meta if isinstance(visual_meta, dict) else {}
    if not meta:
        meta = _visual_meta_from_comments(markdown_text)
    cover = meta.get("cover") if isinstance(meta.get("cover"), dict) else {}
    raw_images = (
        meta.get("body_images")
        or meta.get("images")
        or meta.get("body")
        or []
    )
    body_images = [item for item in raw_images if isinstance(item, dict)]
    return {"cover": cover, "body_images": body_images}


def _prompt_fingerprint(item: dict) -> str:
    source = (
        item.get("prompt_key")
        or item.get("prompt")
        or "|".join(str(item.get(k, "")) for k in ("archetype", "layout", "subject", "type", "style"))
    )
    source = re.sub(r"\s+", " ", str(source)).strip().lower()
    if not source:
        return ""
    return hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]


def build_content_signature(
    markdown_text: str,
    *,
    html_text: str = "",
    title: str = "",
    cover_path: str | Path | None = None,
    visual_meta: dict | None = None,
) -> dict:
    """生成低创作度相似性检查用的轻量结构签名。

    只做启发式归纳，不读外部服务，不阻断发布。签名会写入 publish-history.jsonl，
    供同账号后续文章做近期结构/标题/视觉去重。
    """
    text = _strip_frontmatter(markdown_text or "")
    headings = _extract_md_headings(text) or _extract_html_headings(html_text)
    heading_tokens = [_heading_token(h) for h in headings]
    generic_count = sum(1 for token in heading_tokens if token.startswith("generic:"))
    sequence = _element_sequence(text)
    visual = _normalise_visual_meta(visual_meta, text)
    cover_meta = dict(visual["cover"])
    body_image_meta = [dict(item) for item in visual["body_images"]]
    if cover_meta:
        cover_meta["prompt_fingerprint"] = _prompt_fingerprint(cover_meta)
    for item in body_image_meta:
        item["prompt_fingerprint"] = _prompt_fingerprint(item)
    return {
        "schema": 1,
        "title_pattern": _title_pattern(title),
        "opening_pattern": _opening_pattern(text),
        "structure_archetype": _structure_archetype(text, title, heading_tokens, generic_count),
        "heading_signature": _compact_sequence(heading_tokens, limit=12),
        "generic_heading_count": generic_count,
        "element_sequence": sequence,
        "element_sequence_key": "-".join(sequence[:12]),
        "cover_signature": _cover_signature(cover_path),
        "cover_meta": cover_meta,
        "body_image_meta": body_image_meta,
        "body_image_types": [str(item.get("type") or item.get("archetype") or "").strip() for item in body_image_meta if item.get("type") or item.get("archetype")],
    }


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _history_signature(entry: dict) -> dict | None:
    extra = entry.get("extra") if isinstance(entry.get("extra"), dict) else {}
    sig = extra.get("content_signature") or extra.get("anti_low_quality")
    return sig if isinstance(sig, dict) else None


def _similarity(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, "|".join(a), "|".join(b)).ratio()


def check_low_quality_similarity(
    signature: dict,
    *,
    accounts: list[str],
    history: list[dict] | None = None,
    days: int = 7,
) -> list[dict]:
    """同账号近期低创作度相似性软扫描。

    返回 warning 字典列表，不抛异常、不阻断发布。history 可注入，便于单测。
    """
    warnings: list[dict] = []
    if not signature:
        return warnings

    if signature.get("generic_heading_count", 0) >= 3:
        warnings.append({
            "account": ",".join(accounts) or "unknown",
            "reason": "通用模板小标题过多",
            "detail": "检测到多个“事实底座/背景解释/普通人影响”等模板标题，请改为内容专属小标题。",
            "previous_title": "",
            "previous_ts": "",
        })

    history = list_history(100) if history is None else history
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    account_set = set(accounts or [])

    for entry in reversed(history):
        account = entry.get("account", "")
        if account_set and account not in account_set:
            continue
        ts = _parse_ts(entry.get("ts", ""))
        if ts and ts.astimezone(timezone.utc) < cutoff:
            continue
        old = _history_signature(entry)
        if not old:
            continue

        reasons: list[str] = []
        if signature.get("structure_archetype") == old.get("structure_archetype"):
            reasons.append(f"结构原型重复：{signature.get('structure_archetype')}")
        if signature.get("title_pattern") == old.get("title_pattern") and signature.get("title_pattern") != "direct_statement":
            reasons.append(f"标题句式重复：{signature.get('title_pattern')}")
        if signature.get("opening_pattern") == old.get("opening_pattern") and signature.get("opening_pattern") not in ("unknown", "direct_lead"):
            reasons.append(f"开头方式重复：{signature.get('opening_pattern')}")
        heading_sim = _similarity(signature.get("heading_signature", []), old.get("heading_signature", []))
        if heading_sim >= 0.82 and len(signature.get("heading_signature", [])) >= 2:
            reasons.append(f"小标题骨架相似度 {heading_sim:.2f}")
        if (
            signature.get("element_sequence_key")
            and signature.get("element_sequence_key") == old.get("element_sequence_key")
            and len(signature.get("element_sequence", [])) >= 5
        ):
            reasons.append("段落/表格/列表/图片顺序一致")

        cover_new = signature.get("cover_meta", {})
        cover_old = old.get("cover_meta", {})
        if cover_new and cover_old:
            same_cover_bits = []
            for key, label in (("archetype", "封面原型"), ("layout", "封面构图"), ("subject", "视觉主体")):
                if cover_new.get(key) and cover_new.get(key) == cover_old.get(key):
                    same_cover_bits.append(f"{label}重复：{cover_new.get(key)}")
            if cover_new.get("prompt_fingerprint") and cover_new.get("prompt_fingerprint") == cover_old.get("prompt_fingerprint"):
                same_cover_bits.append("封面生图提示词指纹重复")
            if len(same_cover_bits) >= 2:
                reasons.extend(same_cover_bits)

        image_types_new = signature.get("body_image_types", [])
        image_types_old = old.get("body_image_types", [])
        if image_types_new and image_types_new == image_types_old:
            reasons.append(f"正文图类型顺序重复：{'/'.join(image_types_new)}")

        prompt_keys_new = [item.get("prompt_fingerprint") for item in signature.get("body_image_meta", []) if item.get("prompt_fingerprint")]
        prompt_keys_old = [item.get("prompt_fingerprint") for item in old.get("body_image_meta", []) if item.get("prompt_fingerprint")]
        if prompt_keys_new and prompt_keys_new == prompt_keys_old:
            reasons.append("正文图生图提示词指纹重复")

        if len(reasons) >= 2:
            warnings.append({
                "account": account,
                "reason": "同账号近期内容结构/视觉相似",
                "detail": "；".join(reasons),
                "previous_title": entry.get("title", ""),
                "previous_ts": entry.get("ts", ""),
            })
            break

    return warnings


def print_low_quality_warnings(warnings: list[dict]) -> None:
    if not warnings:
        return
    print("\n⚠ 低创作度相似性软扫描命中（不阻断，请优先重写结构/标题或重做封面）：", file=sys.stderr)
    for item in warnings:
        prev = item.get("previous_title") or "无历史标题"
        ts = item.get("previous_ts") or "当前稿件"
        print(f"  [{item.get('account', '')}] {item.get('reason', '')}: {item.get('detail', '')}", file=sys.stderr)
        print(f"    对比对象: {ts} {prev}", file=sys.stderr)
    print("  → 处理方式：换结构原型、改标题句式、重做封面原型或减少同风格正文图。\n", file=sys.stderr)



def _history_path() -> Path:
    root = ensure_workspace(workspace_root())
    return root / "publish-history.jsonl"


def record_publish(
    *,
    account: str,
    title: str,
    media_id: str,
    job_dir: str = "",
    article_dir: str = "",
    cover: str = "",
    app_id: str = "",
    extra: dict | None = None,
) -> Path:
    """Append one publish event to ~/.hermes/workspaces/wechat/publish-history.jsonl."""
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "account": account,
        "title": title,
        "media_id": media_id,
        "job_dir": job_dir,
        "article_dir": article_dir,
        "cover": cover,
        "app_id_tail": app_id[-4:] if app_id else "",
    }
    if extra:
        entry["extra"] = extra
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def list_history(limit: int = 20) -> list[dict]:
    path = _history_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


if __name__ == "__main__":
    # CLI: show recent history
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--check-file", help="scan a markdown/html file for AI-disclosure phrases")
    a = ap.parse_args()
    if a.check_file:
        text = Path(a.check_file).read_text(encoding="utf-8")
        hits = check_ai_disclosure(text, raise_on_hit=False)
        if not hits:
            print("✓ 未检测到 AI 披露声明")
        else:
            for ln, sn in hits:
                print(f"行 {ln}: {sn}")
            raise SystemExit(2)
    else:
        for e in list_history(a.limit):
            print(f"{e.get('ts','')}  [{e.get('account','')}]  {e.get('title','')[:40]}  media_id={e.get('media_id','')[:16]}...")
