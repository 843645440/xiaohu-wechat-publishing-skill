#!/usr/bin/env python3
"""一键发布管线：排版 → 图片注入 → 发布草稿箱

将分散的 format.py + inject_body_images.py + publish.py 三步
合并为一条命令，消除中间手动修补环节。

核心改进：
1. format.py 排版时自动处理 <!-- img:filename --> 标记
2. 图片文件直接在命令行指定，自动复制到输出目录
3. 封面图必填，缺失直接失败
4. 一条命令从 md 到草稿箱

用法：
    # 完整一键发布
    python3 publish_pipe.py \
      --input article.md \
      --cover cover.png \
      --images hero.png \
      --account xiaocong

    # 仅排版+注入，不推送草稿箱
    python3 publish_pipe.py \
      --input article.md \
      --cover cover.png \
      --images hero.png \
      --dry-run

    # 跳过排版，直接发布已有 article.html
    python3 publish_pipe.py \
      --dir /path/to/article/ \
      --cover cover.png \
      --account yeluzi
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path

from workspace import ensure_workspace, token_cache_path, workspace_root
from image_injector import inject as inject_images, format_stats as format_inject_stats
from publish_history import check_ai_disclosure, check_high_risk, print_high_risk_warnings, record_publish
from runtime import python_bin

# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent

# ── 账号凭据（从 ~/.hermes/.env 自动加载）──────────────────────────────
_ACCOUNTS = {}


def _load_accounts_from_env():
    env_path = Path.home() / ".hermes" / ".env"
    if not env_path.exists():
        return
    env_vars = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env_vars[k.strip()] = v.strip()
    for key, val in env_vars.items():
        if key.startswith("WECHAT_APPID_"):
            suffix = key[len("WECHAT_APPID_"):]
            secret_key = f"WECHAT_SECRET_{suffix}"
            if secret_key in env_vars:
                name = suffix.lower()
                author_key = f"WECHAT_AUTHOR_{suffix}"
                _ACCOUNTS[name] = {
                    "app_id": val,
                    "app_secret": env_vars[secret_key],
                    "author": env_vars.get(author_key, ""),
                }


_load_accounts_from_env()

with open(SKILL_DIR / "config.json", encoding="utf-8") as f:
    CONFIG = json.load(f)

WORKSPACE_ROOT = workspace_root(CONFIG)


# ── ConfigGuard（从 publish.py 移植）──────────────────────────────────
class ConfigGuard:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self._original_content = None

    def __enter__(self):
        if self.config_path.exists():
            self._original_content = self.config_path.read_text(encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._original_content is not None:
            try:
                current = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else None
                if current != self._original_content:
                    self.config_path.write_text(self._original_content, encoding="utf-8")
                    print("  [ConfigGuard] 配置已恢复")
            except Exception as e:
                print(f"  [ConfigGuard] ⚠ 配置恢复失败: {e}")
        if exc_type is not None and not (exc_type is SystemExit and getattr(exc_val, "code", None) == 0):
            print(f"  [ConfigGuard] 检测到异常: {exc_type.__name__}: {exc_val}")
        return False


# ── 微信 API（从 publish.py 移植）─────────────────────────────────────
def _token_cache_path(app_id):
    return token_cache_path(ensure_workspace(WORKSPACE_ROOT), app_id)


def _load_cached_token(app_id):
    cache_path = _token_cache_path(app_id)
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        expires_at = data.get("expires_at", 0)
        if time.time() < expires_at - 300:
            print(f"  token 缓存命中（剩余 {int((expires_at - time.time()) / 60)} 分钟）")
            return data["access_token"]
    except Exception:
        pass
    return None


def _save_cached_token(app_id, access_token, expires_in):
    cache_path = _token_cache_path(app_id)
    data = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in,
        "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_access_token(app_id, app_secret):
    cached = _load_cached_token(app_id)
    if cached:
        return cached

    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    )
    import requests
    resp = requests.get(url, timeout=15)
    data = resp.json()

    if "access_token" in data:
        expires_in = data.get("expires_in", 7200)
        print(f"  token 有效期: {expires_in} 秒")
        _save_cached_token(app_id, data["access_token"], expires_in)
        return data["access_token"]
    else:
        errcode = data.get("errcode", "?")
        errmsg = data.get("errmsg", "未知错误")
        print(f"错误: 获取 access_token 失败 (errcode={errcode}: {errmsg})")
        sys.exit(1)


def upload_thumb_image(token, image_path):
    import requests
    url = (
        "https://api.weixin.qq.com/cgi-bin/material/add_material"
        f"?access_token={token}&type=image"
    )
    filename = os.path.basename(image_path)
    ext = Path(image_path).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
    }.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        files = {"media": (filename, f, content_type)}
        resp = requests.post(url, files=files, timeout=30)

    data = resp.json()
    if "media_id" in data:
        return data["media_id"]
    else:
        print(f"错误: 上传封面图失败 - {data}")
        return None


def upload_content_image(token, image_path, max_retries=3):
    import requests
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    filename = os.path.basename(image_path)
    ext = Path(image_path).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
    }.get(ext, "image/jpeg")

    for attempt in range(1, max_retries + 1):
        try:
            with open(image_path, "rb") as f:
                files = {"media": (filename, f, content_type)}
                resp = requests.post(url, files=files, timeout=30)
            data = resp.json()
            if "url" in data:
                return data["url"]
            else:
                print(f"  ✗ 上传失败 ({attempt}/{max_retries}) - {filename}: {data}")
        except Exception as e:
            print(f"  ✗ 上传异常 ({attempt}/{max_retries}) - {filename}: {e}")
        if attempt < max_retries:
            time.sleep(2 * attempt)
    return None


def replace_all_images(html, article_dir, token):
    """替换 HTML 中的所有图片为微信 CDN URL"""
    import requests
    import html as html_module
    image_dir = article_dir / "images"
    replaced = 0
    failed = 0

    def replace_src(match):
        nonlocal replaced, failed
        src = match.group(1)
        if "mmbiz.qpic.cn" in src:
            return match.group(0)

        # 外部 URL
        if src.startswith(("http://", "https://")):
            try:
                url = html_module.unescape(src)
                resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                ct = resp.headers.get("Content-Type", "")
                ext = ".png" if "png" in ct else ".webp" if "webp" in ct else ".jpg"
                tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                tmp.write(resp.content)
                tmp.close()
                cdn_url = upload_content_image(token, tmp.name)
                os.unlink(tmp.name)
                if cdn_url:
                    replaced += 1
                    print(f"  ✓ 外部图片: {src[:60]}...")
                    return f'src="{cdn_url}"'
            except Exception as e:
                print(f"  ✗ 下载失败: {src[:60]}... ({e})")
            failed += 1
            return match.group(0)

        # 本地图片
        local_path = article_dir / src
        if not local_path.exists() and image_dir.exists():
            local_path = image_dir / os.path.basename(src)
        if local_path.exists():
            cdn_url = upload_content_image(token, str(local_path))
            if cdn_url:
                replaced += 1
                print(f"  ✓ {os.path.basename(src)}")
                return f'src="{cdn_url}"'
            failed += 1
            return match.group(0)
        else:
            print(f"  ✗ 未找到: {src}")
            failed += 1
            return match.group(0)

    html = re.sub(r'src="([^"]+)"', replace_src, html)
    return html, replaced, failed


def push_draft(token, title, content, thumb_media_id, author="", digest=""):
    import requests
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 1,
        }]
    }
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=body,
                         headers={"Content-Type": "application/json"}, timeout=30)
    result = resp.json()
    if "media_id" in result:
        return result["media_id"]
    else:
        print(f"错误: 推送草稿箱失败 - {result}")
        return None


def extract_title_from_html(html):
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return None


def extract_digest_from_html(html, max_len=54):
    """从 HTML 中提取摘要（前 max_len 个纯文字字符）"""
    # 移除所有 HTML 标签
    text = re.sub(r"<[^>]+>", "", html)
    # 移除多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 截取前 max_len 字符
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str]
    warnings: list[str]


ACCOUNT_TITLE_NAMES = {
    "熵增时刻",
    "小葱AI社",
    "小葱 AI 社",
    "思想的野路子丶",
    "思想的野路子",
    "yeluzi",
    "xiaocong",
}


def _strip_html_text(value: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", value or "")).strip()


def _image_sources(html: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r'<img\b[^>]*\bsrc="([^"]+)"', html)]


def _local_image_missing(src: str, article_dir: Path) -> bool:
    if src.startswith(("http://", "https://", "data:")):
        return False
    src_path = Path(src)
    candidates = [article_dir / src_path, article_dir / "images" / src_path.name]
    return not any(p.exists() for p in candidates)


def validate_publish_ready(
    *,
    html: str,
    article_dir: Path,
    cover_path: Path,
    title: str,
    accounts: list[tuple[str, str, str, str]],
    inject_missing: int = 0,
    require_account: bool = True,
) -> ValidationResult:
    """Hard local gate before dry-run success or live draft publishing."""
    issues: list[str] = []
    warnings: list[str] = []
    article_dir = Path(article_dir)
    cover_path = Path(cover_path)
    title_clean = _strip_html_text(title)

    if not (article_dir / "article.html").exists():
        issues.append(f"article.html 不存在: {article_dir / 'article.html'}")
    if not title_clean:
        issues.append("未找到正式标题")
    if title_clean in {re.sub(r"\s+", "", item) for item in ACCOUNT_TITLE_NAMES}:
        issues.append(f"H1/标题疑似账号名而不是正式标题: {title}")
    if re.search(r"<!--\s*img:", html):
        issues.append("仍有未替换的 <!-- img:... --> marker")
    if inject_missing > 0:
        issues.append(f"有 {inject_missing} 个图位图片未找到")
    if not cover_path.exists():
        issues.append(f"封面图不存在: {cover_path}")

    for src in _image_sources(html):
        if _local_image_missing(src, article_dir):
            issues.append(f"HTML 图片文件不存在: {src}")

    if require_account:
        if not accounts:
            issues.append("未指定发布账号")
        for name, app_id, app_secret, _author in accounts:
            if not name:
                issues.append("发布账号名为空")
            if not app_id or not app_secret:
                issues.append(f"账号 {name} 缺少 app_id/app_secret")
    elif not accounts:
        warnings.append("未指定账号；仅适合本地排版检查")

    return ValidationResult(ok=not issues, issues=issues, warnings=warnings)


def print_validation_result(result: ValidationResult) -> None:
    if result.ok:
        print("  OK 发布前硬校验通过")
        for item in result.warnings:
            print(f"  WARN {item}")
        return
    print("\nFAIL 发布前硬校验失败：", file=sys.stderr)
    for issue in result.issues:
        print(f"  - {issue}", file=sys.stderr)
    for item in result.warnings:
        print(f"  WARN {item}", file=sys.stderr)


# ── 图片注入：见 image_injector.py（single source of truth）─────────


# ── 主流程 ────────────────────────────────────────────────────────────
def _resolve_cover(cli_value, input_path, dir_path):
    """智能解析封面：CLI > input 同目录 cover.* > input 父目录 assets/cover.* > article_dir/images/cover.*"""
    if cli_value:
        p = Path(cli_value).expanduser().resolve()
        if not p.exists():
            print(f"错误: 封面图不存在 - {p}", file=sys.stderr)
            sys.exit(1)
        return p
    candidates = []
    bases = []
    if input_path:
        ip = Path(input_path).expanduser().resolve()
        bases += [ip.parent, ip.parent / "assets", ip.parent.parent / "assets"]
    if dir_path:
        dp = Path(dir_path).expanduser().resolve()
        bases += [dp, dp / "images", dp / "assets"]
    for base in bases:
        for ext in ("png", "jpg", "jpeg", "webp"):
            for name in ("cover", "Cover", "COVER"):
                cand = base / f"{name}.{ext}"
                if cand.exists():
                    candidates.append(cand)
    if candidates:
        chosen = candidates[0]
        print(f"  ✓ 自动识别封面: {chosen}")
        return chosen
    print(
        "错误: 未指定 --cover 且未找到默认封面文件\n"
        "  → 请用 --cover <path> 指定，或在 source/ 或 assets/ 下放置 cover.png",
        file=sys.stderr,
    )
    sys.exit(1)


def _run_pipe():
    parser = argparse.ArgumentParser(description="一键发布管线：排版 → 注入 → 发布")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i", help="Markdown 文件路径（自动排版）")
    group.add_argument("--dir", "-d", help="已有排版目录（跳过排版）")
    parser.add_argument("--cover", "-c", help="封面图片路径（不指定时自动搜索 cover.png）")
    parser.add_argument("--images", nargs="*", default=[], help="正文图片文件路径")
    parser.add_argument("--title", "-t", help="文章标题（默认从 HTML 提取）")
    parser.add_argument("--author", "-a", help="作者名")
    parser.add_argument("--theme", default=None, help="排版主题")
    parser.add_argument("--account", help="公众号账号名，可逗号分隔（xiaocong,yeluzi）一次推到多个号")
    parser.add_argument("--job-dir", help="本次任务目录；排版输出会写入该目录下的 format/")
    parser.add_argument("--output-dir", help="排版输出根目录；未设置时读取 config.output_dir")
    parser.add_argument("--dry-run", action="store_true", help="只做本地排版与校验，不触网、不上传、不推送")
    parser.add_argument("--skip-ai-guard", action="store_true",
                        help="跳过 AI 披露声明黑名单检查（不推荐；默认禁用）")
    args = parser.parse_args()

    # ── 0. 解析封面（智能默认）──
    cover_path = _resolve_cover(args.cover, args.input, args.dir)

    # ── 0.5 AI 披露声明硬检查（用户规则）──
    if args.input:
        md_text = Path(args.input).expanduser().resolve().read_text(encoding="utf-8")
        if not args.skip_ai_guard and not os.environ.get("HERMES_WECHAT_SKIP_AI_GUARD"):
            check_ai_disclosure(md_text, raise_on_hit=True)
        else:
            print("  ⚠ AI 披露声明检查已跳过（--skip-ai-guard）")
        # 高风险关键词软扫描（warning 级，不阻断；见 quality-and-risk.md C 节）
        # 标题/封面文案是标题党与敏感词高发区，连同标题一起扫。
        scan_text = ((args.title or "") + "\n" + md_text)
        print_high_risk_warnings(check_high_risk(scan_text))

    # ── 1. 账号设置（支持多账号列表）──
    accounts_to_publish = []  # list of (name, app_id, app_secret, author)
    default_app_id = CONFIG["wechat"].get("app_id", "")
    default_app_secret = CONFIG["wechat"].get("app_secret", "")
    default_author = args.author or ""

    if args.account:
        names = [n.strip() for n in args.account.split(",") if n.strip()]
        bad = [n for n in names if n not in _ACCOUNTS]
        if bad:
            available = ", ".join(sorted(_ACCOUNTS)) or "未发现账号；请检查 ~/.hermes/.env"
            print(f"错误: 未找到账号 {bad}。可用账号: {available}", file=sys.stderr)
            sys.exit(1)
        for n in names:
            acct = _ACCOUNTS[n]
            accounts_to_publish.append((
                n,
                acct["app_id"],
                acct["app_secret"],
                args.author or acct.get("author", ""),
            ))
        print(f"账号: {', '.join(names)}  ({len(accounts_to_publish)} 个)")
    else:
        accounts_to_publish.append(("default", default_app_id, default_app_secret, default_author))
        print(f"账号: config.json 默认 (app_id={default_app_id})")

    # ── 2. 排版 ──
    if args.input:
        theme = args.theme or CONFIG["settings"]["default_theme"]
        input_path = Path(args.input).resolve()

        print(f"\n=== 第一步：排版（主题: {theme}）===")
        if args.job_dir:
            output_base = Path(args.job_dir).expanduser().resolve() / "format"
        elif args.output_dir:
            output_base = Path(args.output_dir).expanduser().resolve()
        else:
            output_base = Path(CONFIG["output_dir"]).expanduser().resolve()
        format_cmd = [
            python_bin(), str(SCRIPT_DIR / "format.py"),
            "--input", str(input_path),
            "--theme", theme,
            "--output", str(output_base),
            "--no-open",
        ]
        result = subprocess.run(format_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"排版失败:\n{result.stderr}")
            sys.exit(1)
        print(result.stdout)

        file_stem = re.sub(r"-(公众号|小红书|微博)$", "", input_path.stem)
        article_dir = output_base / file_stem
    else:
        article_dir = Path(args.dir)

    # 自动下钻子目录
    if not (article_dir / "article.html").exists():
        subdirs = [d for d in article_dir.iterdir() if d.is_dir() and (d / "article.html").exists()]
        if len(subdirs) == 1:
            print(f"  自动定位子目录: {subdirs[0].name}")
            article_dir = subdirs[0]
        elif len(subdirs) > 1:
            print(f"错误: 多个子目录包含 article.html，请明确指定")
            sys.exit(1)

    if not (article_dir / "article.html").exists():
        print(f"错误: 未找到 article.html - {article_dir}")
        sys.exit(1)

    # ── 3. 注入正文图（统一走 image_injector）──
    print(f"\n=== 第二步：图片注入 ===")
    article_html = article_dir / "article.html"
    html = article_html.read_text(encoding="utf-8")
    images_dir = article_dir / "images"
    images_dir.mkdir(exist_ok=True)

    extra_paths = [Path(p) for p in args.images]
    search_paths = [images_dir, article_dir, article_dir.parent / "assets"]
    if args.input:
        search_paths.insert(0, Path(args.input).expanduser().resolve().parent / "assets")
        search_paths.insert(0, Path(args.input).expanduser().resolve().parent)

    html, stats = inject_images(
        html, search_paths,
        extra_files=extra_paths,
        copy_to=images_dir,
        fallback_position=True,
        mode="html",
    )
    print(format_inject_stats(stats))
    if stats.missing > 0:
        print(
            f"  ⚠ 警告：有 {stats.missing} 个图位的图片未找到（保留原 marker）。",
            "发布前硬校验会拦截，请先补图或删除 marker。", sep="\n",
        )

    # 写回 HTML
    article_html.write_text(html, encoding="utf-8")
    img_count = html.count("<img")
    print(f"  HTML 中共 {img_count} 个 <img> 标签")

    # ── 4. 提取标题 ──
    title = args.title or extract_title_from_html(html) or article_dir.name
    print(f"\n=== 第三步：发布 ===")
    print(f"标题: {title}")

    validation = validate_publish_ready(
        html=html,
        article_dir=article_dir,
        cover_path=cover_path,
        title=title,
        accounts=accounts_to_publish,
        inject_missing=stats.missing,
        require_account=not args.dry_run,
    )
    print_validation_result(validation)
    if not validation.ok:
        sys.exit(1)

    if args.dry_run:
        print(f"\n[dry-run] 本地硬校验通过，未获取 token、未上传图片、未推送草稿箱")
        print(f"  目录: {article_dir}")
        print(f"  标题: {title}")
        print(f"  封面: {cover_path}")
        print(f"  HTML 长度: {len(html)} 字符")
        print(f"  HTML 图片数: {img_count}")
        print(f"  目标账号数: {len(accounts_to_publish)}")
        for name, aid, _, author in accounts_to_publish:
            print(f"    - {name} (app_id={aid[-8:] if aid else '<none>'}) author={author}")
        return

    # ── 5-8. 多账号循环：每个账号独立获取 token、上传图、推草稿 ──
    overall_success = 0
    overall_fail = 0
    for acct_name, app_id, app_secret, author in accounts_to_publish:
        print(f"\n{'─'*60}\n推送账号: {acct_name}  作者: {author}\n{'─'*60}")
        try:
            print(f"获取 access_token...")
            token = get_access_token(app_id, app_secret)
            print("✓ token 获取成功")

            # 每个账号都需要重新上传一份图（微信 CDN URL 是 token 绑定的）
            html_for_account = article_html.read_text(encoding="utf-8")
            local_imgs = list(images_dir.iterdir()) if images_dir.exists() else []
            local_count = len([f for f in local_imgs if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp')])
            external_count = len(re.findall(r'src="(https?://[^"]+)"', html_for_account))
            external_count -= len(re.findall(r'src="https?://mmbiz\.qpic\.cn[^"]*"', html_for_account))

            if local_count + external_count > 0:
                print(f"上传正文图片 ({local_count} 本地 + {external_count} 外部)...")
                html_for_account, replaced, failed = replace_all_images(html_for_account, article_dir, token)
                print(f"  上传完成: {replaced} 成功, {failed} 失败")
                if failed > 0 and replaced == 0:
                    print(f"  ✗ [{acct_name}] 所有图片上传失败，跳过该账号")
                    overall_fail += 1
                    continue
            else:
                print("无正文图片需上传")

            print(f"上传封面图: {cover_path.name}")
            thumb_media_id = upload_thumb_image(token, str(cover_path))
            if not thumb_media_id:
                print(f"  ✗ [{acct_name}] 封面上传失败")
                overall_fail += 1
                continue
            print(f"  ✓ media_id: {thumb_media_id[:20]}...")

            print(f"推送到草稿箱...")
            digest = extract_digest_from_html(html_for_account)
            media_id = push_draft(token, title, html_for_account, thumb_media_id, author, digest)
            if not media_id:
                print(f"  ✗ [{acct_name}] 推送失败")
                overall_fail += 1
                continue

            # 归档发布历史
            try:
                hist = record_publish(
                    account=acct_name,
                    title=title,
                    media_id=media_id,
                    job_dir=str(article_dir.parent),
                    article_dir=str(article_dir),
                    cover=str(cover_path),
                    app_id=app_id,
                )
                print(f"  ✓ 已归档到 {hist}")
            except Exception as e:
                print(f"  ⚠ 归档失败: {e}")

            print(f"\n  ✓ [{acct_name}] 发布成功  media_id: {media_id}")
            overall_success += 1
        except SystemExit:
            raise
        except Exception as e:
            print(f"  ✗ [{acct_name}] 异常: {e}")
            overall_fail += 1

    print(f"\n{'='*60}\n  汇总: 成功 {overall_success} / 失败 {overall_fail}  → 草稿箱已就绪\n{'='*60}")
    if overall_success == 0 and overall_fail > 0:
        sys.exit(1)


def main():
    config_path = SKILL_DIR / "config.json"
    with ConfigGuard(config_path):
        _run_pipe()


if __name__ == "__main__":
    main()
