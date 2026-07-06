#!/usr/bin/env python3
"""发布历史、AI 披露硬扫描、高风险软扫描、轻量标题/大意防重。"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

from workspace import ensure_workspace, workspace_root


SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
HIGH_RISK_KEYWORDS_PATH = SKILL_DIR / "data" / "high-risk-keywords.json"

_HIGH_RISK_FALLBACK = [
    "降息", "加息", "抄底", "牛市", "熊市",
    "地缘", "制裁", "领导人",
]


def _load_high_risk_keywords() -> tuple[list[str], dict[str, str]]:
    """从 data/high-risk-keywords.json 加载软扫描关键词。"""
    notes: dict[str, str] = {}
    if not HIGH_RISK_KEYWORDS_PATH.exists():
        print(f"  ⚠ 高风险关键词文件不存在: {HIGH_RISK_KEYWORDS_PATH}，使用内置最小集",
              file=sys.stderr)
        return list(_HIGH_RISK_FALLBACK), notes

    keywords: list[str] = []
    try:
        data = json.loads(HIGH_RISK_KEYWORDS_PATH.read_text(encoding="utf-8"))
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
    """扫描 AI 身份披露。命中时默认 SystemExit(2)。"""
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat in AI_DISCLOSURE_PATTERNS:
            if pat.search(line):
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                hits.append((i, snippet))
                break
    if hits and raise_on_hit:
        print("\n✗ 检测到 AI 身份披露 / 利益相关声明（用户硬规则禁止）：", file=sys.stderr)
        for ln, sn in hits:
            print(f"  行 {ln}: {sn}", file=sys.stderr)
        print("\n  → 请删除上述内容后再发布。AI 披露扫描为发布前硬门禁，不可跳过。",
              file=sys.stderr)
        raise SystemExit(2)
    return hits


def check_high_risk(text: str, *, keywords=None, notes: dict[str, str] | None = None
                    ) -> list[tuple[int, str, str]]:
    """高风险关键词软扫描。只 warning，不阻断。"""
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
                note = notes.get(kw)
                if note:
                    snippet = f"{snippet}  <易误报: {note}>"
                hits.append((i, kw, snippet))
    return hits


def print_high_risk_warnings(hits: list[tuple[int, str, str]]) -> None:
    if not hits:
        return
    print("\n⚠ 高风险关键词软扫描命中（不阻断，请人工确认是否换题/软化切口）：", file=sys.stderr)
    for ln, kw, sn in hits:
        print(f"  行 {ln} [{kw}]: {sn}", file=sys.stderr)
    print("  → 避免政治、财经预测、敏感社会议题和投资建议。\n", file=sys.stderr)


def _history_path() -> Path:
    root = ensure_workspace(workspace_root())
    return root / "publish-history.jsonl"


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4:].lstrip()
    return text


def _plain_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)
    value = re.sub(r"\[[^\]]+\]\([^)]+\)", "", value)
    value = re.sub(r"[#>*_`|~-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def build_content_summary(markdown_text: str, *, html_text: str = "", limit: int = 180) -> str:
    """从正文提取轻量文章大意，用于近期防重归档。"""
    source = _strip_frontmatter(markdown_text or "") or html_text or ""
    text = _plain_text(source)
    if not text:
        return ""
    return text[:limit]


def build_content_signature(
    markdown_text: str,
    *,
    html_text: str = "",
    title: str = "",
    cover_path: str | Path | None = None,
    visual_meta: dict | None = None,
) -> dict:
    """兼容旧调用名：现在只生成标题 + 大意，不做结构/视觉签名。"""
    return {
        "schema": 2,
        "title": _plain_text(title)[:80],
        "summary": build_content_summary(markdown_text, html_text=html_text),
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


def _similarity(a: str, b: str) -> float:
    a = _plain_text(a)
    b = _plain_text(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _entry_summary(entry: dict) -> str:
    if entry.get("summary"):
        return str(entry.get("summary", ""))
    extra = entry.get("extra") if isinstance(entry.get("extra"), dict) else {}
    if extra.get("summary"):
        return str(extra.get("summary", ""))
    sig = extra.get("content_signature") if isinstance(extra.get("content_signature"), dict) else {}
    return str(sig.get("summary", ""))


def check_low_quality_similarity(
    signature: dict,
    *,
    accounts: list[str],
    history: list[dict] | None = None,
    days: int = 14,
) -> list[dict]:
    """轻量同账号防重：只比标题和文章大意。"""
    warnings: list[dict] = []
    if not signature:
        return warnings

    title = str(signature.get("title", ""))
    summary = str(signature.get("summary", ""))
    history = list_history(100) if history is None else history
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    account_set = set(accounts or [])

    for entry in reversed(history):
        account = entry.get("account", "")
        if account_set and account not in account_set:
            continue
        ts = _parse_ts(entry.get("ts", ""))
        if ts and ts.astimezone(timezone.utc) < cutoff:
            continue

        title_sim = _similarity(title, str(entry.get("title", "")))
        summary_sim = _similarity(summary, _entry_summary(entry))
        reasons = []
        if title_sim >= 0.86:
            reasons.append(f"标题相似度 {title_sim:.2f}")
        if summary_sim >= 0.72 and len(summary) >= 40:
            reasons.append(f"文章大意相似度 {summary_sim:.2f}")
        if reasons:
            warnings.append({
                "account": account,
                "reason": "同账号近期标题/大意相似",
                "detail": "；".join(reasons),
                "previous_title": entry.get("title", ""),
                "previous_ts": entry.get("ts", ""),
            })
            break

    return warnings


def print_low_quality_warnings(warnings: list[dict]) -> None:
    if not warnings:
        return
    print("\n⚠ 近期标题/文章大意相似（不阻断；cron 可配置为命中即停）：", file=sys.stderr)
    for item in warnings:
        prev = item.get("previous_title") or "无历史标题"
        ts = item.get("previous_ts") or "未知时间"
        print(f"  [{item.get('account', '')}] {item.get('detail', '')}", file=sys.stderr)
        print(f"    对比对象: {ts} {prev}", file=sys.stderr)
    print("  → 处理方式：换题，或把文章大意改成明显不同的新角度。\n", file=sys.stderr)


def record_publish(
    *,
    account: str,
    title: str,
    media_id: str,
    summary: str = "",
    job_dir: str = "",
    article_dir: str = "",
    cover: str = "",
    app_id: str = "",
    extra: dict | None = None,
) -> Path:
    """只归档最小历史：账号、标题、文章大意和 media_id。"""
    if not summary and isinstance(extra, dict):
        sig = extra.get("content_signature") if isinstance(extra.get("content_signature"), dict) else {}
        summary = str(sig.get("summary", ""))
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "account": account,
        "title": title,
        "summary": summary[:220],
        "media_id": media_id,
    }
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
            print(f"{e.get('ts','')}  [{e.get('account','')}]  {e.get('title','')[:40]}  {e.get('summary','')[:60]}")
