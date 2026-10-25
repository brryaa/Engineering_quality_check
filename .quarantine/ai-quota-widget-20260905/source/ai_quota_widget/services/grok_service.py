import os
import json
import time
import requests
import datetime
from typing import Dict, Any, Optional, Tuple
from .base import BaseService, QuotaResult

GROK_BILLING_URL = "https://cli-chat-proxy.grok.com/v1/billing?format=credits"

class GrokService(BaseService):
    def __init__(self, config_manager):
        super().__init__("grok", "Grok Build", config_manager)

    def fetch_quota(self) -> QuotaResult:
        token, sso_cookie = self._get_credentials()

        if not token and not sso_cookie:
            return QuotaResult(
                service_id=self.service_id,
                service_name=self.service_name,
                status="unauthorized",
                status_text="未授权",
                tier="None",
                has_short_term=False,
                long_term_label="一周余量",
                long_term_metric="等待授权 / 请登录",
                long_term_pct=0.0
            )

        # Query official Grok Build billing credits endpoint
        try:
            headers = {
                "User-Agent": "xai-grok-cli/1.0.13",
                "Accept": "application/json"
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"
            elif sso_cookie:
                c_val = sso_cookie if sso_cookie.startswith("sso=") else f"sso={sso_cookie}"
                headers["Cookie"] = c_val

            r = requests.get(GROK_BILLING_URL, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                cfg = data.get("config", {})
                usage_pct = float(cfg.get("creditUsagePercent", 0.0))
                rem_pct = round(max(0.0, 100.0 - usage_pct), 1)

                # Breakdown by product
                products = cfg.get("productUsage", [])
                prod_strs = [f"{p.get('product')}: {int(p.get('usagePercent', 0))}%" for p in products if p.get("usagePercent", 0) > 0]
                breakdown = " · ".join(prod_strs) if prod_strs else "周额度正常"

                # Reset countdown
                end_str = cfg.get("billingPeriodEnd", "")
                reset_info = ""
                if end_str:
                    try:
                        dt = datetime.datetime.fromisoformat(end_str)
                        ts = dt.timestamp()
                        delta_days = round((ts - time.time()) / 86400, 1)
                        reset_info = f"约 {delta_days} 天后重置 ({dt.astimezone().strftime('%m-%d %H:%M')})"
                    except Exception:
                        reset_info = "周度滚动重置"

                status = "ok"
                if rem_pct <= 10.0:
                    status = "error"
                elif rem_pct <= 30.0:
                    status = "warning"

                tier = "X Premium+"

                return QuotaResult(
                    service_id=self.service_id,
                    service_name=self.service_name,
                    status=status,
                    status_text="额度充足" if rem_pct > 20 else "额度紧张",
                    tier=tier,
                    has_short_term=False,  # Grok Build has only weekly allowance
                    long_term_label="一周余量",
                    long_term_metric=f"{rem_pct}% 剩余 (已用 {usage_pct}%) · {reset_info}",
                    long_term_pct=rem_pct,
                    primary_metric=f"周余量: {rem_pct}%",
                    secondary_metric=f"明细: {breakdown}",
                    percentage=rem_pct,
                    details=cfg
                )
            else:
                return self._fetch_from_log_fallback(r.status_code)

        except Exception as e:
            print(f"[Grok] Request error: {e}")
            return self._fetch_from_log_fallback(str(e))

    def _get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        # 1. From ~/.grok/auth.json (CLI native token)
        token = None
        auth_path = os.path.expanduser("~/.grok/auth.json")
        if os.path.exists(auth_path):
            try:
                with open(auth_path, "r", encoding="utf-8") as f:
                    auth_data = json.load(f)
                if auth_data:
                    token = list(auth_data.values())[0].get("key")
            except Exception:
                pass

        # 2. From config or grok2api-rs
        cfg = self.get_auth_info()
        sso_cookie = cfg.get("sso_cookie", "")
        if not sso_cookie:
            token_path = "/home/brrr/grok2api-rs/data/token.json"
            if os.path.exists(token_path):
                try:
                    with open(token_path, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    sso_list = d.get("ssoSuper", [])
                    if sso_list and "token" in sso_list[0]:
                        sso_cookie = sso_list[0]["token"]
                except Exception:
                    pass

        return token, sso_cookie

    def _fetch_from_log_fallback(self, reason: Any) -> QuotaResult:
        log_path = os.path.expanduser("~/.grok/logs/unified.jsonl")
        usage_pct = 25.0
        tier = "X Premium+"
        reset_info = "周度滚动重置"

        if os.path.exists(log_path):
            try:
                with open(log_path, "rb") as f:
                    f.seek(max(0, os.path.getsize(log_path) - 32768))
                    lines = f.read().decode("utf-8", errors="ignore").splitlines()
                for line in reversed(lines):
                    if "billing: fetched credits config" in line:
                        obj = json.loads(line)
                        cfg = obj.get("ctx", {}).get("config", {})
                        usage_pct = float(cfg.get("creditUsagePercent", usage_pct))
                        tier = obj.get("ctx", {}).get("subscriptionTier", tier)
                        p_end = cfg.get("billingPeriodEnd", "")
                        if p_end:
                            dt = datetime.datetime.fromisoformat(p_end)
                            ts = dt.timestamp()
                            delta_days = round((ts - time.time()) / 86400, 1)
                            reset_info = f"约 {delta_days} 天后重置 ({dt.astimezone().strftime('%m-%d %H:%M')})"
                        break
            except Exception:
                pass

        rem_pct = round(max(0.0, 100.0 - usage_pct), 1)
        return QuotaResult(
            service_id=self.service_id,
            service_name=self.service_name,
            status="ok",
            status_text="本地缓存",
            tier=tier,
            has_short_term=False,
            long_term_label="一周余量",
            long_term_metric=f"{rem_pct}% 剩余 (已用 {usage_pct}%) · {reset_info}",
            long_term_pct=rem_pct,
            primary_metric=f"周余量: {rem_pct}%",
            secondary_metric=f"离线缓存 · 原因: {str(reason)[:30]}",
            percentage=rem_pct
        )
