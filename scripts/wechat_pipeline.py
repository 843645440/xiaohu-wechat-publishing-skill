#!/usr/bin/env python3
"""Managed job workspace for WeChat article production.

This wrapper keeps every article run inside one job directory so Hermes does
not scatter previews, images, token caches, and temporary files across /tmp.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from workspace import (
    account_root,
    ensure_workspace,
    job_root,
    new_job_id,
    slugify,
    workspace_root,
    write_manifest,
)
from runtime import python_bin


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG = json.loads((SKILL_DIR / "config.json").read_text(encoding="utf-8"))


def _copy(src, dst):
    src = Path(src).expanduser().resolve()
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return dst


def _find_article_dir(base):
    base = Path(base)
    if (base / "article.html").exists():
        return base
    matches = [p.parent for p in base.rglob("article.html")]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return None
    raise SystemExit("找到多个 article.html，请用 --dir 指定明确目录:\n" + "\n".join(str(p) for p in matches))


def _extract_title(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if not m:
        return ""
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()


def cmd_build(args):
    root = ensure_workspace(workspace_root(CONFIG))
    input_path = Path(args.input).expanduser().resolve()
    slug = slugify(args.slug or input_path.stem)
    job_id = args.job_id or new_job_id(slug)
    account = args.account or "manual"
    acct_dir = account_root(root, job_id, account)
    source_dir = acct_dir / "source"
    asset_dir = source_dir / "assets"
    source_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)

    article_copy = _copy(input_path, source_dir / "article.md")
    copied_images = []
    for image in args.images or []:
        copied_images.append(str(_copy(image, asset_dir / Path(image).name)))
    cover_copy = None
    if args.cover:
        cover_copy = _copy(args.cover, asset_dir / "cover" / Path(args.cover).name)

    output_base = acct_dir / "format"
    format_cmd = [
        python_bin(),
        str(SCRIPT_DIR / "format.py"),
        "--input",
        str(article_copy),
        "--theme",
        args.theme or CONFIG.get("settings", {}).get("default_theme", "newspaper"),
        "--output",
        str(output_base),
        "--no-open",
    ]
    env = os_environ()
    env["WECHAT_WORKSPACE_DIR"] = str(root)
    result = subprocess.run(format_cmd, text=True, capture_output=True, env=env)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    sys.stdout.write(result.stdout)

    article_dir = _find_article_dir(output_base)
    manifest = {
        "job_id": job_id,
        "account": account,
        "status": "built",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": str(article_copy),
        "article_dir": str(article_dir) if article_dir else "",
        "cover": str(cover_copy) if cover_copy else "",
        "images": copied_images,
        "theme": args.theme or CONFIG.get("settings", {}).get("default_theme", "newspaper"),
    }
    write_manifest(acct_dir, manifest)
    print(f"\njob: {job_id}")
    print(f"account_dir: {acct_dir}")
    if article_dir:
        print(f"article_dir: {article_dir}")


def os_environ():
    import os

    return os.environ.copy()


def cmd_validate(args):
    target = Path(args.dir).expanduser().resolve()
    article_dir = _find_article_dir(target)
    if not article_dir:
        raise SystemExit(f"未找到 article.html: {target}")
    html_path = article_dir / "article.html"
    html = html_path.read_text(encoding="utf-8")
    issues = []
    title = _extract_title(html)
    if not title:
        issues.append("未找到 H1 标题")
    if re.search(r"<!--\s*img:", html):
        issues.append("仍有未替换的 <!-- img:... --> marker")
    img_count = html.count("<img")

    cover = Path(args.cover).expanduser().resolve() if args.cover else None
    if not cover:
        image_dir = article_dir / "images"
        covers = []
        if image_dir.exists():
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"):
                covers.extend(image_dir.glob(f"cover*{ext[1:]}"))
        if covers:
            cover = covers[0]
    if not cover or not cover.exists():
        issues.append("缺少封面图；请指定 --cover 或放入 images/cover.png")

    report = {
        "ok": not issues,
        "article_dir": str(article_dir),
        "title": title,
        "img_count": img_count,
        "cover": str(cover) if cover else "",
        "issues": issues,
    }
    report_path = target / "validation.json" if target.is_dir() else article_dir / "validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


def cmd_publish(args):
    target = Path(args.dir).expanduser().resolve()
    article_dir = _find_article_dir(target)
    if not article_dir:
        raise SystemExit(f"未找到 article.html: {target}")
    cmd = [
        python_bin(),
        str(SCRIPT_DIR / "publish_pipe.py"),
        "--dir",
        str(article_dir),
        "--cover",
        str(Path(args.cover).expanduser().resolve()),
    ]
    if args.account:
        cmd += ["--account", args.account]
    if args.title:
        cmd += ["--title", args.title]
    if args.author:
        cmd += ["--author", args.author]
    if args.dry_run:
        cmd += ["--dry-run"]
    env = os_environ()
    env["WECHAT_WORKSPACE_DIR"] = str(ensure_workspace(workspace_root(CONFIG)))
    raise SystemExit(subprocess.call(cmd, env=env))


def cmd_clean(args):
    root = ensure_workspace(workspace_root(CONFIG))
    cutoff = time.time() - args.days * 86400
    jobs_dir = root / "jobs"
    removed = 0
    for path in sorted(jobs_dir.iterdir() if jobs_dir.exists() else []):
        if not path.is_dir():
            continue
        if path.stat().st_mtime >= cutoff:
            continue
        if args.dry_run:
            print(f"[dry-run] remove {path}")
        else:
            shutil.rmtree(str(path))
            print(f"removed {path}")
        removed += 1
    print(f"matched: {removed}")


def main():
    parser = argparse.ArgumentParser(description="Hermes WeChat managed pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build", help="创建 job 并在 job 目录内完成本地排版")
    build.add_argument("--input", required=True)
    build.add_argument("--account", default="manual")
    build.add_argument("--slug")
    build.add_argument("--job-id")
    build.add_argument("--theme")
    build.add_argument("--cover")
    build.add_argument("--images", nargs="*", default=[])
    build.set_defaults(func=cmd_build)

    validate = sub.add_parser("validate", help="校验本地 article.html、图位和封面")
    validate.add_argument("--dir", required=True)
    validate.add_argument("--cover")
    validate.set_defaults(func=cmd_validate)

    publish = sub.add_parser("publish", help="发布已通过校验的 article_dir")
    publish.add_argument("--dir", required=True)
    publish.add_argument("--cover", required=True)
    publish.add_argument("--account")
    publish.add_argument("--title")
    publish.add_argument("--author")
    publish.add_argument("--dry-run", action="store_true")
    publish.set_defaults(func=cmd_publish)

    clean = sub.add_parser("clean", help="删除过期 job 目录")
    clean.add_argument("--days", type=int, default=7)
    clean.add_argument("--dry-run", action="store_true")
    clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
