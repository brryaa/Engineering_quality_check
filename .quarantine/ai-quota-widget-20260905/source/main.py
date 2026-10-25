#!/usr/bin/env python3
import sys
import os
import argparse
import webbrowser

# Add current directory to python path
cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

from ai_quota_widget.config import ConfigManager
from ai_quota_widget.services import CodexService, AgyService, GrokService

def run_cli_status():
    print("=" * 55)
    print("        🔮 AI 算力余量监控 (CLI 快速查询)       ")
    print("=" * 55)

    cfg = ConfigManager()
    services = {
        "codex": CodexService(cfg),
        "agy": AgyService(cfg),
        "grok": GrokService(cfg)
    }

    for s_id, svc in services.items():
        try:
            q = svc.fetch_quota()
            icon = {"codex": "🤖", "agy": "🚀", "grok": "⚡"}.get(s_id, "💡")
            print(f"\n{icon} 【{svc.service_name}】 [{q.tier}]")
            print(f"   状态: {q.status_text}")
            print(f"   余量: {q.primary_metric}")
            print(f"   周期: {q.secondary_metric}")
            print(f"   比例: [{'#' * int(q.percentage // 5)}{'.' * (20 - int(q.percentage // 5))}] {q.percentage}%")
        except Exception as e:
            print(f"\n❌ 【{svc.service_name}】 查询失败: {e}")

    print("\n" + "=" * 55)

def run_browser_auth(service_name: str):
    from ai_quota_widget.auth_server import AuthServer, DEFAULT_PORT
    cfg = ConfigManager()
    server = AuthServer(cfg, lambda s: print(f"✅ 授权完成: {s}"))
    server.start()

    url = server.get_auth_url(service_name)
    print(f"正在打开浏览器授权页: {url}")
    webbrowser.open(url)
    print("请在浏览器中完成登录并提交凭证。按 Ctrl+C 退出...")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("\n已退出授权服务。")

def main():
    parser = argparse.ArgumentParser(description="AI 算力余量桌面浮窗小程序 (Codex, AGY, Grok Build)")
    parser.add_argument("--status", action="store_true", help="在终端打印当前各服务余量信息")
    parser.add_argument("--auth", choices=["codex", "agy", "grok"], help="启动指定服务的浏览器授权页")
    args = parser.parse_args()

    if args.status:
        run_cli_status()
        return

    if args.auth:
        run_browser_auth(args.auth)
        return

    # Start GUI floating window
    from ai_quota_widget.app import Application
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
