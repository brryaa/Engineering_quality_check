import json
import os
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional

DEFAULT_PORT = 18899

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Quota Hub - 浏览器授权助手</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-green: #238636;
            --accent-green-hover: #2ea043;
            --accent-blue: #1f6feb;
            --accent-blue-hover: #388bfd;
            --accent-orange: #d29922;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            max-width: 540px;
            width: 100%;
            padding: 32px;
            box-shadow: 0 16px 36px rgba(0,0,0,0.5);
        }
        .header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }
        .icon { font-size: 32px; }
        h1 { font-size: 22px; font-weight: 600; }
        p.desc {
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .step {
            background: #21262d;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 14px;
            font-size: 14px;
        }
        .step-num {
            display: inline-block;
            background: #30363d;
            color: #fff;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            text-align: center;
            line-height: 22px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }
        .btn {
            display: inline-block;
            text-decoration: none;
            cursor: pointer;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            transition: all 0.2s;
            text-align: center;
        }
        .btn-primary { background-color: var(--accent-blue); color: white; }
        .btn-primary:hover { background-color: var(--accent-blue-hover); }
        .btn-success { background-color: var(--accent-green); color: white; width: 100%; margin-top: 14px; }
        .btn-success:hover { background-color: var(--accent-green-hover); }
        .btn-outline {
            background-color: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            margin-top: 8px;
            width: 100%;
        }
        .btn-outline:hover { background-color: #30363d; }
        textarea, input[type="text"] {
            width: 100%;
            background: #0d1117;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 10px;
            color: #fff;
            font-family: monospace;
            font-size: 13px;
            margin-top: 8px;
            resize: vertical;
        }
        textarea:focus, input[type="text"]:focus {
            outline: none;
            border-color: var(--accent-blue);
        }
        .alert-box {
            display: none;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            font-size: 14px;
            line-height: 1.5;
        }
        .alert-success { background: #1f6f4333; border: 1px solid #238636; color: #3fb950; }
        .alert-error { background: #da363333; border: 1px solid #f85149; color: #ff7b72; }
        .footer {
            margin-top: 24px;
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">{{SERVICE_ICON}}</div>
            <div>
                <h1>{{SERVICE_TITLE}} - 浏览器授权</h1>
                <span style="font-size: 12px; color: var(--text-secondary);">服务ID: {{SERVICE_ID}}</span>
            </div>
        </div>

        <p class="desc">{{SERVICE_DESC}}</p>

        <div class="step">
            <span class="step-num">1</span><strong>登录服务网页</strong>
            <div style="margin-top: 8px;">
                <a href="{{OFFICIAL_LOGIN_URL}}" target="_blank" class="btn btn-primary">
                    在新标签页打开 {{SERVICE_TITLE}} 登录页 ↗
                </a>
            </div>
        </div>

        <div class="step">
            <span class="step-num">2</span><strong>输入授权凭证 (Cookie / Token / Key)</strong>
            <form id="authForm" onsubmit="submitAuth(event)">
                <textarea id="credential" rows="4" placeholder="{{PLACEHOLDER}}" required></textarea>
                <button type="submit" class="btn btn-success">✅ 保存并授权至桌面浮窗</button>
            </form>
        </div>

        {{LOCAL_ACTION_HTML}}

        <div id="alertBox" class="alert-box"></div>

        <div class="footer">
            AI Quota Floating Widget · 本地安全回环 127.0.0.1:{{PORT}}
        </div>
    </div>

    <script>
        async function submitAuth(e) {
            e.preventDefault();
            const val = document.getElementById('credential').value.trim();
            if (!val) return;
            const alertBox = document.getElementById('alertBox');
            try {
                const res = await fetch('/api/auth/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        service: '{{SERVICE_ID}}',
                        credential: val
                    })
                });
                const data = await res.json();
                if (data.ok) {
                    alertBox.className = 'alert-box alert-success';
                    alertBox.style.display = 'block';
                    alertBox.innerHTML = '🎉 <strong>授权成功！</strong> 凭证已同步至桌面浮窗小程序，正在刷新余量中...<br>您可以关闭此网页回到桌面。';
                } else {
                    alertBox.className = 'alert-box alert-error';
                    alertBox.style.display = 'block';
                    alertBox.innerHTML = '❌ 授权保存失败: ' + (data.error || '未知错误');
                }
            } catch (err) {
                alertBox.className = 'alert-box alert-error';
                alertBox.style.display = 'block';
                alertBox.innerHTML = '❌ 网络请求错误: ' + err.message;
            }
        }

        async function syncLocal(service) {
            const alertBox = document.getElementById('alertBox');
            try {
                const res = await fetch('/api/auth/sync-local', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ service: service })
                });
                const data = await res.json();
                if (data.ok) {
                    alertBox.className = 'alert-box alert-success';
                    alertBox.style.display = 'block';
                    alertBox.innerHTML = '🎉 <strong>本机现有授权同步成功！</strong> 浮窗小程序已更新。';
                } else {
                    alertBox.className = 'alert-box alert-error';
                    alertBox.style.display = 'block';
                    alertBox.innerHTML = '❌ 本机同步失败: ' + (data.error || '未检测到配置');
                }
            } catch (err) {
                alertBox.className = 'alert-box alert-error';
                alertBox.style.display = 'block';
                alertBox.innerHTML = '❌ 网络请求错误: ' + err.message;
            }
        }
    </script>
</body>
</html>
"""


class AuthServerHandler(BaseHTTPRequestHandler):
    config_manager = None
    on_auth_callback: Optional[Callable[[str], None]] = None

    def log_message(self, format, *args):
        pass  # Suppress default noisy console logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/auth", "/auth/"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """<!DOCTYPE html>
            <html><head><meta charset="utf-8"><title>AI Quota Hub 授权</title>
            <style>body{background:#0d1117;color:#fff;font-family:sans-serif;padding:40px;text-align:center;}
            a{color:#58a6ff;margin:10px;display:inline-block;font-size:18px;text-decoration:none;background:#21262d;padding:12px 24px;border-radius:8px;}
            a:hover{background:#30363d;}</style></head><body>
            <h2>AI Quota Hub 浏览器授权中心</h2><p style="color:#8b949e;margin:20px;">请选择需要授权的服务：</p>
            <a href="/auth/codex">🟢 Codex (ChatGPT) 授权</a>
            <a href="/auth/agy">🔵 AGY (Antigravity) 授权</a>
            <a href="/auth/grok">🟠 Grok Build 授权</a>
            </body></html>"""
            self.wfile.write(html.encode("utf-8"))
            return

        if path.startswith("/auth/"):
            service = path.split("/")[2].lower()
            self._render_auth_page(service)
            return

        if path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"running"}')
            return

        self.send_response(404)
        self.end_headers()

    def _render_auth_page(self, service: str):
        metadata = {
            "codex": {
                "icon": "🤖",
                "title": "Codex (ChatGPT)",
                "desc": "您可以在此进行 Codex / ChatGPT 网页授权。登录后将 Session Token 或 Cookie 填入下方，或一键使用本机已安装 App 的现成 API。",
                "url": "https://chatgpt.com",
                "placeholder": "粘贴 ChatGPT 的 session token、cookie 或 access token...",
                "local_action": """<div class="step">
                    <span class="step-num">★</span><strong>快捷方式：已安装 App 现成 API</strong>
                    <p style="color: var(--text-secondary); font-size: 13px; margin: 6px 0 10px;">
                        检测到本机已安装 Codex / ChatGPT 客户端并保存了登录状态，可直接使用现成 API 授权。
                    </p>
                    <button type="button" onclick="syncLocal('codex')" class="btn btn-outline">
                        💻 一键从本机已安装 App 读取现成 API
                    </button>
                </div>"""
            },
            "grok": {
                "icon": "⚡",
                "title": "Grok Build (xAI)",
                "desc": "您可以在此进行 Grok Build / xAI 网页授权。登录 grok.com 后复制 Cookie 中的 sso 字段填入下方即可查询余量。",
                "url": "https://grok.com",
                "placeholder": "粘贴 grok.com 的 sso cookie (例如: sso=eyJ0eXAi...)",
                "local_action": """<div class="step">
                    <span class="step-num">★</span><strong>快捷方式：本机 Grok 凭证</strong>
                    <p style="color: var(--text-secondary); font-size: 13px; margin: 6px 0 10px;">
                        本机环境中检测到 Grok Token/SSO 凭据，可直接一键读取。
                    </p>
                    <button type="button" onclick="syncLocal('grok')" class="btn btn-outline">
                        💻 一键从本机读取 Grok 凭证
                    </button>
                </div>"""
            },
            "agy": {
                "icon": "🚀",
                "title": "AGY (Antigravity)",
                "desc": "您可以在此进行 Google Antigravity / Gemini 授权。登录 Google AI Studio 或 Antigravity 后将 API Key 或 Token 填入下方。",
                "url": "https://aistudio.google.com/app/apikey",
                "placeholder": "粘贴 Gemini API Key 或 Antigravity OAuth Token...",
                "local_action": """<div class="step">
                    <span class="step-num">★</span><strong>快捷方式：本机 AGY CLI 配置</strong>
                    <p style="color: var(--text-secondary); font-size: 13px; margin: 6px 0 10px;">
                        本机当前正在运行 Antigravity CLI (agy)，可直接同步本地环境配置。
                    </p>
                    <button type="button" onclick="syncLocal('agy')" class="btn btn-outline">
                        💻 一键同步本机 AGY CLI 配置
                    </button>
                </div>"""
            }
        }

        meta = metadata.get(service, metadata["codex"])
        html = HTML_TEMPLATE
        html = html.replace("{{SERVICE_ICON}}", meta["icon"])
        html = html.replace("{{SERVICE_TITLE}}", meta["title"])
        html = html.replace("{{SERVICE_ID}}", service)
        html = html.replace("{{SERVICE_DESC}}", meta["desc"])
        html = html.replace("{{OFFICIAL_LOGIN_URL}}", meta["url"])
        html = html.replace("{{PLACEHOLDER}}", meta["placeholder"])
        html = html.replace("{{LOCAL_ACTION_HTML}}", meta["local_action"])
        html = html.replace("{{PORT}}", str(DEFAULT_PORT))

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path == "/api/auth/submit":
            service = payload.get("service", "").lower()
            credential = payload.get("credential", "").strip()

            if not service or not credential:
                self._send_json({"ok": False, "error": "缺少凭据信息"}, 400)
                return

            if AuthServerHandler.config_manager:
                if service == "codex":
                    if "session-token=" in credential:
                        AuthServerHandler.config_manager.update_service_config("codex", {
                            "auth_mode": "browser",
                            "cookie": credential
                        })
                    elif credential.startswith("eyJ"):
                        AuthServerHandler.config_manager.update_service_config("codex", {
                            "auth_mode": "browser",
                            "access_token": credential
                        })
                    else:
                        AuthServerHandler.config_manager.update_service_config("codex", {
                            "auth_mode": "browser",
                            "cookie": credential
                        })
                elif service == "grok":
                    if not credential.startswith("sso=") and credential.startswith("eyJ"):
                        credential = f"sso={credential}"
                    AuthServerHandler.config_manager.update_service_config("grok", {
                        "auth_mode": "browser",
                        "sso_cookie": credential
                    })
                elif service == "agy":
                    if credential.startswith("AIza"):
                        AuthServerHandler.config_manager.update_service_config("agy", {
                            "auth_mode": "browser",
                            "api_key": credential
                        })
                    else:
                        AuthServerHandler.config_manager.update_service_config("agy", {
                            "auth_mode": "browser",
                            "oauth_token": credential
                        })

                if AuthServerHandler.on_auth_callback:
                    AuthServerHandler.on_auth_callback(service)

            self._send_json({"ok": True})
            return

        elif self.path == "/api/auth/sync-local":
            service = payload.get("service", "").lower()
            if AuthServerHandler.config_manager:
                if service == "codex":
                    AuthServerHandler.config_manager.update_service_config("codex", {"auth_mode": "app"})
                elif service == "grok":
                    # Load from token.json or auth.json
                    token_path = "/home/brrr/grok2api-rs/data/token.json"
                    if os.path.exists(token_path):
                        with open(token_path) as f:
                            gdata = json.load(f)
                        sso_list = gdata.get("ssoSuper", [])
                        if sso_list and "token" in sso_list[0]:
                            AuthServerHandler.config_manager.update_service_config("grok", {
                                "auth_mode": "browser",
                                "sso_cookie": f"sso={sso_list[0]['token']}"
                            })
                elif service == "agy":
                    AuthServerHandler.config_manager.update_service_config("agy", {"auth_mode": "local"})

                if AuthServerHandler.on_auth_callback:
                    AuthServerHandler.on_auth_callback(service)

            self._send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data: dict, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


class AuthServer:
    def __init__(self, config_manager, on_auth_callback: Optional[Callable[[str], None]] = None, port: int = DEFAULT_PORT):
        AuthServerHandler.config_manager = config_manager
        AuthServerHandler.on_auth_callback = on_auth_callback
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        AuthServerHandler.config_manager = AuthServerHandler.config_manager
        AuthServerHandler.on_auth_callback = AuthServerHandler.on_auth_callback
        try:
            self.server = HTTPServer(("127.0.0.1", self.port), AuthServerHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"[AuthServer] Browser authorization receiver started on http://127.0.0.1:{self.port}")
        except Exception as e:
            print(f"[AuthServer] Failed to start auth server: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    def get_auth_url(self, service: str) -> str:
        return f"http://127.0.0.1:{self.port}/auth/{service}"
