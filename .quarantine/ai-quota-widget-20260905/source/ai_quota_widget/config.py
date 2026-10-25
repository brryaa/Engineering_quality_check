import json
import os
import stat
from typing import Dict, Any

CONFIG_DIR = os.path.expanduser("~/.config/ai-quota-widget")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "refresh_interval": 300,  # 5 minutes
        "always_on_top": True,
        "mini_mode": False,
        "opacity": 0.96,
        "window_x": 980,
        "window_y": 60,
        "theme": "dark"
    },
    "services": {
        "codex": {
            "name": "Codex (ChatGPT)",
            "auth_mode": "app",  # 'app' (installed app API) or 'browser' (browser auth)
            "access_token": "",
            "session_token": "",
            "account_id": "",
            "cookie": "",
            "last_quota": {}
        },
        "agy": {
            "name": "AGY (Antigravity)",
            "auth_mode": "local",  # 'local' (local CLI) or 'browser' (browser auth)
            "api_key": "",
            "oauth_token": "",
            "model": "Gemini 3.8 Flash (High)",
            "last_quota": {}
        },
        "grok": {
            "name": "Grok Build",
            "auth_mode": "browser",  # 'browser' (sso cookie) or 'local' (local grok config)
            "sso_cookie": "",
            "model_name": "grok-3",
            "last_quota": {}
        }
    }
}


class ConfigManager:
    def get(self, key: str, default=None):
        parts = key.split('.')
        curr = self.config
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return default
        return curr

    def __init__(self):
        self.config_path = CONFIG_FILE
        self.config = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    # Merge with default config
                    for sec in ["app", "services"]:
                        if sec not in cfg:
                            cfg[sec] = DEFAULT_CONFIG[sec]
                    for s_id, s_cfg in DEFAULT_CONFIG["services"].items():
                        if s_id not in cfg["services"]:
                            cfg["services"][s_id] = s_cfg
                    return cfg
            except Exception as e:
                print(f"[Config] Error loading config: {e}, recreating default")

        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        # Pre-seed credentials from local system if available
        self._auto_detect_local_environment(cfg)
        self._save_to_disk(cfg)
        return cfg

    def _auto_detect_local_environment(self, cfg: Dict[str, Any]):
        # 1. Codex: check ~/.codex/auth.json
        codex_auth = os.path.expanduser("~/.codex/auth.json")
        if os.path.exists(codex_auth):
            try:
                with open(codex_auth, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                tokens = cdata.get("tokens", {})
                cfg["services"]["codex"]["auth_mode"] = "app"
                cfg["services"]["codex"]["access_token"] = tokens.get("access_token", "")
                cfg["services"]["codex"]["account_id"] = tokens.get("account_id", "")
                print("[Config] Auto-detected local Codex App configuration!")
            except Exception as e:
                print(f"[Config] Failed auto-detecting Codex: {e}")

        # 2. Grok: check grok2api-rs or ~/.grok/auth.json
        grok_token_file = "/home/brrr/grok2api-rs/data/token.json"
        if os.path.exists(grok_token_file):
            try:
                with open(grok_token_file, "r", encoding="utf-8") as f:
                    gdata = json.load(f)
                sso_list = gdata.get("ssoSuper", [])
                if sso_list and "token" in sso_list[0]:
                    sso_tok = sso_list[0]["token"]
                    cfg["services"]["grok"]["sso_cookie"] = f"sso={sso_tok}"
                    print("[Config] Auto-detected Grok SSO cookie from local environment!")
            except Exception as e:
                print(f"[Config] Failed auto-detecting Grok: {e}")

        # 3. AGY: check ~/.gemini/antigravity-cli/settings.json
        agy_settings = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
        if os.path.exists(agy_settings):
            try:
                with open(agy_settings, "r", encoding="utf-8") as f:
                    adata = json.load(f)
                if "model" in adata:
                    cfg["services"]["agy"]["model"] = adata["model"]
                cfg["services"]["agy"]["auth_mode"] = "local"
                print("[Config] Auto-detected local AGY configuration!")
            except Exception as e:
                print(f"[Config] Failed auto-detecting AGY: {e}")

    def _save_to_disk(self, cfg: Dict[str, Any]):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            # Secure permissions: readable/writable only by user
            os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            print(f"[Config] Failed saving config to disk: {e}")

    def save(self):
        self._save_to_disk(self.config)

    def get_app_config(self) -> Dict[str, Any]:
        return self.config.get("app", {})

    def update_app_config(self, updates: Dict[str, Any]):
        self.config.setdefault("app", {}).update(updates)
        self.save()

    def get_service_config(self, service_id: str) -> Dict[str, Any]:
        return self.config.get("services", {}).get(service_id, {})

    def update_service_config(self, service_id: str, updates: Dict[str, Any]):
        self.config.setdefault("services", {}).setdefault(service_id, {}).update(updates)
        self.save()
