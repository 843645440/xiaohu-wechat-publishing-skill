#!/usr/bin/env python3
"""Shared workspace helpers for the WeChat publishing skill."""

import json
import os
import re
import time
from pathlib import Path


DEFAULT_WORKSPACE = "~/.hermes/workspaces/wechat"


def load_config(skill_dir):
    config_path = Path(skill_dir) / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def workspace_root(config=None):
    config = config or {}
    raw = (
        os.environ.get("WECHAT_WORKSPACE_DIR")
        or config.get("workspace_dir")
        or DEFAULT_WORKSPACE
    )
    path = Path(raw).expanduser()
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def ensure_workspace(root):
    root = Path(root).expanduser().resolve()
    for name in ("jobs", "cache", "cache/tokens", "tmp", "trash"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def slugify(value, fallback="article"):
    value = (value or "").strip().lower()
    value = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", value)
    value = re.sub(r"-(公众号|小红书|微博)$", "", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    return value or fallback


def new_job_id(slug=None):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    clean = slugify(slug or "job", "job")
    return f"{stamp}-{clean}"


def job_root(root, job_id):
    return Path(root) / "jobs" / job_id


def account_root(root, job_id, account):
    return job_root(root, job_id) / account


def token_cache_path(root, app_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", app_id or "unknown")
    return Path(root) / "cache" / "tokens" / f"wechat_token_{safe}.json"


def selection_file(root):
    return Path(root) / "cache" / "selected-theme.txt"


def manifest_path(job_dir):
    return Path(job_dir) / "manifest.json"


def write_manifest(job_dir, manifest):
    path = manifest_path(job_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
