#!/usr/bin/env python3
"""Publish history archive and persona safety guard.

Functions:
    record_publish(...)      → append jsonl line to ~/.hermes/workspaces/wechat/publish-history.jsonl
    list_history(limit=20)   → most recent N entries
    check_ai_disclosure(text, *, raise_on_hit=True) → returns list of (line_no, snippet);
        by default raises SystemExit(2) when any pattern matches.

User-level invariant (from user profile memory):
  公众号文章严禁出现"本文由AI协助撰写"之类的AI身份披露/利益相关声明.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from workspace import ensure_workspace, workspace_root


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
            "\n  → 请删除上述内容后再发布。",
            "若确认是误报，可设置环境变量 HERMES_WECHAT_SKIP_AI_GUARD=1 跳过（不推荐）。",
            sep="\n", file=sys.stderr,
        )
        raise SystemExit(2)
    return hits


# 高风险关键词（政治/财经/敏感）软扫描——命中只告警、不阻断。
# 规则来源：prompts/quality-and-risk.md C 节。命中应改"对普通人影响"软切口或换题。
HIGH_RISK_KEYWORDS = [
    # 货币 / 财政 / 监管政策走向
    "降息", "加息", "货币政策", "财政政策", "监管收紧", "政策转向", "政策信号",
    # 市场预测 / 投资建议
    "抄底", "牛市", "熊市", "涨停", "跌停", "暴跌", "唱多", "唱空", "买入", "卖出", "点位",
    # 敏感时政 / 地缘 / 社会
    "地缘", "制裁", "站队", "脱钩", "领导人", "群体事件", "维权", "罢工",
]


def check_high_risk(text: str, *, keywords=None) -> list[tuple[int, str, str]]:
    """Soft-scan text for high-risk (politics/finance/sensitive) keywords.

    Warning-only — NEVER raises or blocks. Returns [(line_no, keyword, snippet)].
    Callers should print these as warnings and ask a human to confirm the angle.
    """
    kws = list(keywords) if keywords is not None else HIGH_RISK_KEYWORDS
    hits: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for kw in kws:
            if kw and kw in line:
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
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
