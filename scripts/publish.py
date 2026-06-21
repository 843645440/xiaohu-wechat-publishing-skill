#!/usr/bin/env python3
"""微信公众号草稿箱发布工具

将 format.py 排版后的文章推送到微信公众号草稿箱。

用法:
    # 发布排版好的文章目录
    python3 publish.py --dir /path/to/formatted/article/

    # 指定封面图
    python3 publish.py --dir /path/to/formatted/article/ --cover cover.jpg

    # 直接从 Markdown 一步到位（自动排版+发布）
    python3 publish.py --input article.md --theme elegant
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import tempfile
from pathlib import Path

import html as html_module

try:
    import requests
except ImportError:
    requests = None

from workspace import ensure_workspace, selection_file, token_cache_path, workspace_root

# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent

# ── 账号凭据表（从 ~/.hermes/.env 自动加载）────────────────────────────
_ACCOUNTS = {}  # {account_name: {app_id, app_secret, author}}

def _load_accounts_from_env():
    """从 ~/.hermes/.env 读取 WECHAT_APPID_* / WECHAT_SECRET_* 变量构建账号表"""
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

    # 自动发现账号：WECHAT_APPID_<NAME> + WECHAT_SECRET_<NAME>
    seen = set()
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
                seen.add(suffix)

_load_accounts_from_env()

# 先加载 config.json 作为默认
with open(SKILL_DIR / "config.json", encoding="utf-8") as f:
CONFIG = json.load(f)

WORKSPACE_ROOT = workspace_root(CONFIG)


def _require_requests():
    if requests is None:
        print("错误: 缺少 Python 依赖 requests；请先运行 python3 -m pip install --upgrade -r requirements.txt")
        sys.exit(1)
    return requests


# ── 微信 API ─────────────────────────────────────────────────────────
def _token_cache_path():
    """根据当前 app_id 生成 token 缓存文件路径，避免双账号串用"""
    wechat = CONFIG.get("wechat", {})
    app_id = wechat.get("app_id", "unknown")
    return token_cache_path(ensure_workspace(WORKSPACE_ROOT), app_id)


def _load_cached_token():
    """尝试从本地缓存读取有效 token"""
    cache_path = _token_cache_path()
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        expires_at = data.get("expires_at", 0)
        # 提前 5 分钟过期，留安全余量
        if time.time() < expires_at - 300:
            print(f"  token 缓存命中（剩余 {int((expires_at - time.time()) / 60)} 分钟）")
            return data["access_token"]
    except Exception:
        pass
    return None


def _save_cached_token(access_token, expires_in):
    """缓存 token 到本地文件"""
    cache_path = _token_cache_path()
    data = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in,
        "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_access_token():
    """获取微信 API access_token（优先本地缓存，缓存命中不浪费 API 配额）"""
    # 优先读缓存
    cached = _load_cached_token()
    if cached:
        return cached

    wechat = CONFIG.get("wechat", {})
    app_id = wechat.get("app_id")
    app_secret = wechat.get("app_secret")

    if not app_id or not app_secret:
        print("错误: config.json 中未配置 wechat.app_id 或 wechat.app_secret")
        sys.exit(1)

    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    )
    resp = requests.get(url, timeout=15)
    data = resp.json()

    if "access_token" in data:
        expires_in = data.get("expires_in", 7200)
        print(f"  token 有效期: {expires_in} 秒")
        # 缓存到本地
        _save_cached_token(data["access_token"], expires_in)
        return data["access_token"]
    else:
        errcode = data.get("errcode", "?")
        errmsg = data.get("errmsg", "未知错误")
        print(f"错误: 获取 access_token 失败 (errcode={errcode}: {errmsg})")
        if errcode == 40164:
            print("  → IP 不在白名单中，请到公众号后台添加当前 IP")
        elif errcode in (40001, 40125):
            print("  → AppSecret 无效，请检查 config.json 中的 app_secret")
            # token 可能已被其他端刷新导致失效，清除缓存后重试一次
            cache_path = _token_cache_path()
            if cache_path.exists():
                cache_path.unlink()
                print("  → 已清除本地 token 缓存，下次将重新获取")
        sys.exit(1)


def upload_thumb_image(token, image_path):
    """上传封面图到永久素材库，返回 media_id"""
    url = (
        "https://api.weixin.qq.com/cgi-bin/material/add_material"
        f"?access_token={token}&type=image"
    )

    filename = os.path.basename(image_path)
    ext = Path(image_path).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
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


# ── 素材管理 ──────────────────────────────────────────────────────────
def cleanup_stale_materials(token, keep_days=7, dry_run=False):
    """清理永久素材库中超过 keep_days 天的旧素材（封面图堆积问题）

    微信永久素材上限 10 万张，每次发布都会新增一张封面图。
    此函数按页遍历素材列表，删除超过 keep_days 天未使用的旧素材。

    Args:
        token: access_token
        keep_days: 保留最近 N 天的素材，默认 7 天
        dry_run: True 只统计不删除

    Returns:
        deleted_count: 删除的素材数量
    """
    url = "https://api.weixin.qq.com/cgi-bin/material/batchget_material"
    cutoff = time.time() - keep_days * 86400

    deleted = 0
    kept = 0
    offset = 0
    count = 20  # 每页最多 20 条

    print(f"\n--- 素材清理扫描（保留 {keep_days} 天内素材，dry_run={dry_run}）---")

    while True:
        body = {"type": "image", "offset": offset, "count": count}
        resp = requests.post(
            f"{url}?access_token={token}",
            json=body, timeout=15
        )
        data = resp.json()

        items = data.get("item", [])
        if not items:
            break

        for item in items:
            media_id = item["media_id"]
            update_time = item.get("update_time", 0)

            if update_time < cutoff:
                age_days = int((time.time() - update_time) / 86400)
                if dry_run:
                    print(f"  [dry-run] 将删除: {media_id[:20]}... ({age_days} 天前)")
                else:
                    del_url = (
                        "https://api.weixin.qq.com/cgi-bin/material/del_material"
                        f"?access_token={token}"
                    )
                    del_resp = requests.post(
                        del_url,
                        json={"media_id": media_id}, timeout=10
                    )
                    del_data = del_resp.json()
                    if del_data.get("errcode", 0) == 0:
                        print(f"  ✓ 已删除: {media_id[:20]}... ({age_days} 天前)")
                    else:
                        print(f"  ✗ 删除失败: {media_id[:20]}... {del_data}")
                deleted += 1
            else:
                kept += 1

        offset += count
        total = data.get("total_count", 0)
        if offset >= total:
            break

    print(f"--- 扫描完成: {deleted} 个可清理, {kept} 个保留 ---")
    return deleted


def upload_content_image(token, image_path, max_retries=3):
    """上传正文图片（返回 CDN URL），失败自动重试"""
    import time
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"

    filename = os.path.basename(image_path)
    ext = Path(image_path).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
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
            time.sleep(2 * attempt)  # 递增等待

    print(f"  ✗ 上传彻底失败 - {filename}")
    return None


def download_external_image(url):
    """下载外部图片到临时文件，返回本地路径"""
    try:
        # 还原 HTML 实体（&amp; → &）
        url = html_module.unescape(url)
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0"
        })
        resp.raise_for_status()

        # 从 URL 或 Content-Type 推断扩展名
        content_type = resp.headers.get("Content-Type", "")
        if "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            ext = ".jpg"

        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"  ✗ 下载失败: {url[:60]}... ({e})")
        return None


def replace_all_images(html, article_dir, token):
    """替换 HTML 中的所有图片（本地+外部）为微信 CDN URL"""
    image_dir = article_dir / "images"
    replaced = 0
    failed = 0

    def replace_src(match):
        nonlocal replaced, failed
        src = match.group(1)

        # 已经是微信 CDN 的图片，跳过
        if "mmbiz.qpic.cn" in src:
            return match.group(0)

        # 外部 URL：先下载再上传
        if src.startswith("http://") or src.startswith("https://"):
            local_path = download_external_image(src)
            if local_path:
                cdn_url = upload_content_image(token, local_path)
                os.unlink(local_path)  # 清理临时文件
                if cdn_url:
                    replaced += 1
                    print(f"  ✓ 外部图片: {src[:60]}...")
                    return f'src="{cdn_url}"'
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
            else:
                failed += 1
                return match.group(0)
        else:
            print(f"  ✗ 未找到: {src}")
            failed += 1
            return match.group(0)

    html = re.sub(r'src="([^"]+)"', replace_src, html)
    return html, replaced, failed


def push_draft(token, title, content, thumb_media_id, author=""):
    """推送文章到草稿箱"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

    data = {
        "articles": [
            {
                "title": title,
                "author": author,
                "content": content,
                "content_source_url": "",
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }

    # 必须用 ensure_ascii=False，否则中文被转义为 \uXXXX 导致微信计算标题长度错误
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=body,
                         headers={"Content-Type": "application/json"}, timeout=30)
    result = resp.json()

    if "media_id" in result:
        return result["media_id"]
    else:
        errcode = result.get("errcode", "?")
        errmsg = result.get("errmsg", "未知错误")
        print(f"错误: 推送草稿箱失败 (errcode={errcode}: {errmsg})")
        return None


# ── 辅助函数 ──────────────────────────────────────────────────────────
def extract_title_from_html(html):
    """从 HTML 中提取 h1 标题"""
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return None


def find_cover_image(article_dir, cover_arg=None):
    """找到封面图路径"""
    if cover_arg:
        p = Path(cover_arg)
        if p.exists():
            return p
        # 尝试在 article_dir 下找
        p = article_dir / cover_arg
        if p.exists():
            return p
        print(f"警告: 指定的封面图不存在: {cover_arg}")
        print("错误: 显式传入了 --cover，但该路径无效。为避免误用正文第一张图作为封面，发布已中止。")
        print("  → 请先确保正式封面已复制到最终发布目录，例如 <article_dir>/images/cover.png")
        sys.exit(1)

    # 在 images/ 目录下找封面图
    image_dir = article_dir / "images"
    if image_dir.exists():
        # 优先找 cover- 开头的文件
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.gif"):
            covers = sorted(image_dir.glob(f"cover*{ext[1:]}"))
            if covers:
                return covers[0]
        print("错误: 未显式传入 --cover，且 images/ 目录下也未找到 cover* 文件。")
        print("  → 为避免误用正文图作为封面，发布已中止。")
        print("  → 请将正式封面放到 <article_dir>/images/cover.png 后重试。")
        sys.exit(1)

    print("错误: 未找到 images/ 目录，无法确定封面图。")
    print("  → 请先生成并同步正式封面到 <article_dir>/images/cover.png")
    sys.exit(1)


# ── 配置安全 ─────────────────────────────────────────────────────────
class ConfigGuard:
    """配置文件安全守卫：无论 publish.py 正常结束还是异常崩溃，都保证恢复原始 config.json

    用法：
        with ConfigGuard(config_path):
            # 在这里安全地修改 config.json（如切换账号）
            main()
        # 退出 with 块时，config.json 已自动恢复
    """

    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.backup_path = self.config_path.with_suffix(
            f".bak.{time.strftime('%Y%m%d_%H%M%S')}"
        )
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
            print(f"\n  [ConfigGuard] 检测到异常: {exc_type.__name__}: {exc_val}")
            print(f"  [ConfigGuard] 配置已安全恢复，异常将被重新抛出")
        return False  # 不吞异常，让调用方看到真实错误


# ── 主流程 ────────────────────────────────────────────────────────────
def _run_publish():
    """实际发布逻辑（由 main 调用，被 ConfigGuard 包裹）"""
    parser = argparse.ArgumentParser(description="微信公众号草稿箱发布工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", "-d", help="format.py 的输出目录（含 article.html 和 images/）")
    group.add_argument("--input", "-i", help="Markdown 文件路径（自动调用 format.py 排版后发布）")
    parser.add_argument("--cover", "-c", help="封面图片路径")
    parser.add_argument("--title", "-t", help="文章标题（默认从 HTML 提取）")
    parser.add_argument("--theme", default=None,
                        help="排版主题（仅 --input 模式有效，默认读取 gallery 选中的主题）")
    parser.add_argument("--author", "-a",
                        default=CONFIG.get("wechat", {}).get("author", ""),
                        help="作者名")
    parser.add_argument("--account",
                        help="公众号账号名（从 ~/.hermes/.env 自动读取凭据，无需手动改 config.json）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只做本地排版与校验，不触网、不上传、不推送")
    args = parser.parse_args()

    # ── 0. 账号切换 ──────────────────────────────────────────────────
    if args.account:
        if args.account not in _ACCOUNTS:
            available = ", ".join(sorted(_ACCOUNTS)) or "未发现账号；请检查 ~/.hermes/.env"
            print(f"错误: 未找到账号 '{args.account}'。可用账号: {available}")
            sys.exit(1)
        acct = _ACCOUNTS[args.account]
        CONFIG["wechat"]["app_id"] = acct["app_id"]
        CONFIG["wechat"]["app_secret"] = acct["app_secret"]
        if acct.get("author"):
            args.author = args.author or acct["author"]
        print(f"账号: {args.account} (app_id={acct['app_id']})")
    else:
        # 兼容旧流程：直接用 config.json 里的凭据
        print(f"账号: config.json 默认 (app_id={CONFIG['wechat'].get('app_id','?')})")

    # ── 1. 确定文章目录 ──────────────────────────────────────────────
    if args.input:
        # 确定主题：优先命令行指定 > gallery 选中 > 默认
        theme = args.theme
        if not theme:
            gallery_theme_file = selection_file(WORKSPACE_ROOT)
            if gallery_theme_file.exists():
                saved = gallery_theme_file.read_text(encoding="utf-8").strip()
                if saved:
                    theme = saved
                    print(f"  使用 gallery 选中的主题: {theme}")
        if not theme:
            theme = CONFIG["settings"]["default_theme"]

        # 先调用 format.py 排版
        input_path = Path(args.input).resolve()
        print(f"=== 第一步：排版 ===")
        format_cmd = [
            sys.executable, str(SCRIPT_DIR / "format.py"),
            "--input", str(input_path),
            "--theme", theme,
            "--no-open",
        ]
        result = subprocess.run(format_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"排版失败:\n{result.stderr}")
            sys.exit(1)
        print(result.stdout)

        # 从 format.py 输出中找到目录
        output_base = Path(CONFIG["output_dir"])
        file_stem = re.sub(r"-(公众号|小红书|微博)$", "", input_path.stem)
        article_dir = output_base / file_stem
    else:
        article_dir = Path(args.dir)

    if not article_dir.exists():
        print(f"错误: 目录不存在 - {article_dir}")
        sys.exit(1)

    # 自动下钻：如果 --dir 指向的目录没有 article.html，检查子目录
    if not (article_dir / "article.html").exists():
        subdirs = [d for d in article_dir.iterdir() if d.is_dir() and (d / "article.html").exists()]
        if len(subdirs) == 1:
            print(f"  自动定位子目录: {subdirs[0].name}")
            article_dir = subdirs[0]
        elif len(subdirs) > 1:
            print(f"错误: {article_dir} 下有多个子目录包含 article.html，请明确指定：")
            for d in subdirs:
                print(f"  {d}")
            sys.exit(1)

    # ── 2. 读取文章 HTML ─────────────────────────────────────────────
    print(f"\n=== {'第二步' if args.input else '第一步'}：准备发布 ===")
    article_path = article_dir / "article.html"

    if not article_path.exists():
        # 兼容旧版：从 preview.html 提取
        preview_path = article_dir / "preview.html"
        if preview_path.exists():
            print("未找到 article.html，从 preview.html 提取...")
            preview_content = preview_path.read_text(encoding="utf-8")
            match = re.search(
                r'<div id="wechatHtml">(.*?)</div>\s*<script>',
                preview_content, re.DOTALL
            )
            if match:
                html = match.group(1).strip()
            else:
                print("错误: 无法从 preview.html 提取文章内容")
                sys.exit(1)
        else:
            print(f"错误: 未找到 article.html 或 preview.html")
            sys.exit(1)
    else:
        html = article_path.read_text(encoding="utf-8")

    # ── 3. 提取标题 ──────────────────────────────────────────────────
    title = args.title or extract_title_from_html(html) or article_dir.name
    author = args.author
    print(f"标题: {title}")
    print(f"作者: {author}")

    # ── 4. 本地发布前校验 ─────────────────────────────────────────────
    cover_path = find_cover_image(article_dir, args.cover)
    if not cover_path:
        print("\n错误: 微信要求必须有封面图。")
        print("  请用 --cover 指定封面图路径，或在 images/ 目录放 cover.png")
        sys.exit(1)

    if args.dry_run:
        img_count = html.count("<img")
        print(f"\n[dry-run] 本地校验通过，未获取 token、未上传图片、未推送草稿箱")
        print(f"  目录: {article_dir}")
        print(f"  标题: {title}")
        print(f"  封面: {cover_path}")
        print(f"  HTML 长度: {len(html)} 字符")
        print(f"  HTML 图片数: {img_count}")
        return

    # ── 5. 获取 token ────────────────────────────────────────────────
    print(f"\n获取 access_token...")
    token = get_access_token()
    print("✓ token 获取成功")

    # ── 6. 上传正文图片 ──────────────────────────────────────────────
    # 统计图片数量（本地 + 外部）
    image_dir = article_dir / "images"
    local_count = len(list(image_dir.iterdir())) if image_dir.exists() else 0
    external_count = len(re.findall(r'src="(https?://[^"]+)"', html))
    # 排除已是微信 CDN 的
    external_count -= len(re.findall(r'src="https?://mmbiz\.qpic\.cn[^"]*"', html))
    total_images = local_count + external_count

    if total_images > 0:
        print(f"\n上传正文图片 ({local_count} 本地 + {external_count} 外部)...")
        html, replaced, failed = replace_all_images(html, article_dir, token)
        print(f"  上传完成: {replaced} 成功, {failed} 失败")
        if failed > 0 and replaced == 0:
            print("  错误: 所有图片上传失败，中止发布（不推空图草稿）")
            sys.exit(1)
        elif failed > 0:
            print("  警告: 部分图片上传失败，文章中对应位置可能显示空白")
            resp = input("  继续发布？(y/N) ").strip().lower()
            if resp != "y":
                print("  已中止")
                sys.exit(0)
    else:
        print("\n无正文图片需上传")

    # ── 7. 上传封面图 ────────────────────────────────────────────────
    print(f"\n上传封面图: {cover_path.name}")
    thumb_media_id = upload_thumb_image(token, str(cover_path))
    if thumb_media_id:
        print(f"  ✓ media_id: {thumb_media_id[:20]}...")
    else:
        print("  ✗ 封面上传失败")
        thumb_media_id = None

    if not thumb_media_id:
        print("\n错误: 微信要求必须有封面图。")
        print("  请用 --cover 指定封面图路径，或在 images/ 目录放一张图片")
        sys.exit(1)

    # ── 8. 推送草稿箱 ────────────────────────────────────────────────
    print(f"\n推送到草稿箱...")
    media_id = push_draft(token, title, html, thumb_media_id, author)

    if media_id:
        print(f"\n{'='*40}")
        print(f"  发布成功!")
        print(f"  草稿 media_id: {media_id}")
        print(f"  → 请到微信公众号后台 → 草稿箱 查看和发布")
        print(f"{'='*40}")
    else:
        print(f"\n发布失败")
        sys.exit(1)


def main():
    """入口：用 ConfigGuard 包裹整个发布流程，保证 config.json 崩溃安全
    
    注意：使用 --account 时凭据来自 ~/.hermes/.env 的内存态，ConfigGuard 
    仍然保护 config.json 不被意外修改（例如 --input 模式写入 output_dir 等）。
    """
    config_path = SKILL_DIR / "config.json"
    with ConfigGuard(config_path):
        _run_publish()


if __name__ == "__main__":
    main()
