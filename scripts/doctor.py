#!/usr/bin/env python3
"""Environment and package checks for the WeChat publishing skill.

Output is agent-friendly: every FAIL line is followed by a `# fix:` block
with a copy-paste shell command that resolves it.
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from workspace import ensure_workspace, workspace_root
from render_editorial_cover import find_system_browser, load_presets


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def check(condition, ok, fail, failures, fix=None):
    if condition:
        print(f"OK   {ok}")
    else:
        print(f"FAIL {fail}")
        if fix:
            print(f"     # fix: {fix}")
        failures.append((fail, fix or ""))


def mode_requires_accounts(mode):
    return mode in ("publish", "all")


def main():
    parser = argparse.ArgumentParser(description="Check WeChat skill runtime health.")
    parser.add_argument(
        "--mode",
        choices=["format", "publish", "all"],
        default="all",
        help="format checks local rendering only; publish also requires WeChat accounts.",
    )
    args = parser.parse_args()

    failures = []
    warnings = []
    config_path = SKILL_DIR / "config.json"
    check(
        config_path.exists(),
        "config.json exists",
        "config.json missing",
        failures,
        fix=f"cp {SKILL_DIR}/config.example.json {config_path}",
    )
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    root = ensure_workspace(workspace_root(config))
    check(root.exists(), f"workspace exists: {root}", f"workspace missing: {root}", failures,
          fix=f"mkdir -p {root}/jobs {root}/cache/tokens {root}/tmp")

    py_ok = sys.version_info >= (3, 9)
    check(py_ok, f"python {sys.version.split()[0]}",
          "Python 3.9+ required; Python 3.12+ recommended",
          failures,
          fix="install Python 3.12+ via pyenv, Homebrew, apt, or system package manager")

    # Detect which python has the required modules (uses runtime.python_bin)
    try:
        from runtime import python_bin
        bin_path = python_bin()
        print(f"INFO detected python_bin = {bin_path}")
        required_mods = ["markdown"]
        if mode_requires_accounts(args.mode):
            required_mods.append("requests")
        for module in required_mods:
            r = subprocess.run([bin_path, "-c", f"import importlib.util,sys; sys.exit(0 if importlib.util.find_spec({module!r}) else 1)"],
                               capture_output=True, timeout=5)
            has = (r.returncode == 0)
            check(has, f"module {module} (in {bin_path})", f"missing module {module} in {bin_path}",
                  failures,
                  fix=f"{bin_path} -m pip install --user --break-system-packages {module}")
    except Exception as e:
        print(f"WARN runtime.python_bin probe failed: {e}")
        fallback_mods = ["markdown"]
        if mode_requires_accounts(args.mode):
            fallback_mods.append("requests")
        for module in fallback_mods:
            check(
                importlib.util.find_spec(module) is not None,
                f"module {module}",
                f"missing module {module}",
                failures,
                fix=f"python3 -m pip install --user --break-system-packages {module}",
            )

    browser_check_ok = True
    browser_hint = ""
    system_browser = find_system_browser()
    if importlib.util.find_spec("playwright") is not None:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                executable = p.chromium.executable_path
                if not executable or not Path(executable).exists():
                    browser_check_ok = False
                    browser_hint = "playwright chromium not installed"
        except Exception as exc:
            browser_check_ok = False
            browser_hint = f"playwright browser check failed: {exc}"
    elif system_browser:
        browser_check_ok = True
        browser_hint = f"system browser fallback: {system_browser}"
    else:
        browser_check_ok = False
        browser_hint = "no Python Playwright and no system Chrome/Chromium fallback found"
    check(
        browser_check_ok,
        browser_hint or "cover renderer browser available",
        browser_hint or "cover renderer browser missing",
        failures,
        fix=f"{sys.executable} -m playwright install chromium  # or install Google Chrome/Chromium",
    )

    themes_dir = SKILL_DIR / "themes"
    theme_count = len(list(themes_dir.glob("*.json"))) if themes_dir.exists() else 0
    check(theme_count > 0, f"themes available: {theme_count}", "themes directory is empty/missing",
          failures, fix=f"ls {themes_dir}  # if missing, re-install skill via skillhub")

    for template in ("preview.html", "gallery.html", "cover-magazine-v1.html"):
        check((SKILL_DIR / "templates" / template).exists(),
              f"template {template}", f"missing template {template}",
              failures, fix=f"# re-install skill: skillhub --dir ~/.hermes/skills install xiaohu-wechat-publishing")

    preset_path = SKILL_DIR / "templates" / "cover-preset-pool.json"
    preset_exists = preset_path.exists()
    check(
        preset_exists,
        "cover preset pool",
        "missing cover-preset-pool.json",
        failures,
        fix=f"# re-install skill: skillhub --dir ~/.hermes/skills install xiaohu-wechat-publishing",
    )
    if preset_exists:
        try:
            preset_count = len(load_presets())
            check(
                preset_count > 0,
                f"cover presets available: {preset_count}",
                "cover preset pool has no presets",
                failures,
                fix=f"# restore presets in {preset_path}",
            )
        except (Exception, SystemExit) as exc:
            check(
                False,
                "cover preset pool valid",
                f"invalid cover preset pool: {exc}",
                failures,
                fix=f"python3 -m json.tool {preset_path}",
            )

    env_path = Path.home() / ".hermes" / ".env"
    env_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    account_count = sum(1 for line in env_text.splitlines() if line.startswith("WECHAT_APPID_"))
    if mode_requires_accounts(args.mode):
        check(
            account_count > 0,
            f"wechat accounts in ~/.hermes/.env: {account_count}",
            "no WECHAT_APPID_* found in ~/.hermes/.env",
            failures,
            fix="# add to ~/.hermes/.env:\n     # WECHAT_APPID_XIAOCONG=wx...\n     # WECHAT_SECRET_XIAOCONG=...\n     # WECHAT_AUTHOR_XIAOCONG=熵增时刻",
        )
    else:
        if account_count > 0:
            print(f"OK   wechat accounts in ~/.hermes/.env: {account_count}")
        else:
            print("WARN no WECHAT_APPID_* found in ~/.hermes/.env (ignored in --mode format)")

    linux_font = Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
    if sys.platform == "darwin":
        print("WARN linux font check skipped on macOS; cover template uses system Chinese fallbacks")
    elif os.name == "nt":
        print("WARN linux font check skipped on Windows")
    else:
        check(linux_font.exists(), f"font exists: {linux_font}", f"missing font: {linux_font}",
              failures, fix="sudo apt install -y fonts-wqy-zenhei fonts-wqy-microhei && fc-cache -fv")

    # Proxy reachability hint (non-fatal)
    if os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY"):
        print(f"INFO https_proxy = {os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')}")
    else:
        print("INFO no https_proxy set (fine for WeChat API; needed only for fetching non-CN resources)")

    if not env_path.exists():
        warnings.append("~/.hermes/.env 不存在；纯排版可继续，但发布与多账号切换不可用")
    elif account_count == 0:
        warnings.append("~/.hermes/.env 未配置 WECHAT_APPID_*；纯排版可继续，但发布不可用")

    if failures:
        print("\nDoctor found problems:")
        for item, fix in failures:
            print(f"- {item}")
            if fix:
                print(f"  fix: {fix}")
        if warnings:
            print("\nDoctor warnings:")
            for item in warnings:
                print(f"- {item}")
        raise SystemExit(1)
    if warnings:
        print("\nDoctor warnings:")
        for item in warnings:
            print(f"- {item}")
    print("\nDoctor passed.")


if __name__ == "__main__":
    main()
