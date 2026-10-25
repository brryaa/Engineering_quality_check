import os
import json
import time
import subprocess
import webbrowser
from typing import Dict, Any, Optional
from .base import BaseService, QuotaResult

class CodexService(BaseService):
    def __init__(self, config_manager):
        super().__init__("codex", "Codex (ChatGPT)", config_manager)
        self._cached_result = None
        self._last_fetch_time = 0

    def fetch_quota(self) -> QuotaResult:
        now = time.time()
        # Cache for 20 seconds to avoid launching process too frequently
        if self._cached_result and (now - self._last_fetch_time < 20):
            return self._cached_result

        result = self._fetch_from_app_server()
        if result:
            self._cached_result = result
            self._last_fetch_time = now
            return result

        # Fallback to local auth.json inspection if app-server fails
        return self._fetch_fallback()

    def _fetch_from_app_server(self) -> Optional[QuotaResult]:
        """Query official codex app-server JSON-RPC for 5h and 7-day rate limits."""
        codex_bin = "/usr/lib/chatgpt/resources/codex"
        if not os.path.exists(codex_bin):
            codex_bin = "codex"

        try:
            p = subprocess.Popen(
                [codex_bin, "app-server", "--listen", "stdio://"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 1. Initialize
            init_req = json.dumps({
                "id": "0",
                "method": "initialize",
                "params": {"clientInfo": {"name": "ai-quota-widget", "version": "1.0"}}
            }) + "\n"
            p.stdin.write(init_req)
            p.stdin.flush()

            # Wait for init
            start = time.time()
            while time.time() - start < 3:
                line = p.stdout.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                    if data.get("id") == "0":
                        break
                except Exception:
                    pass

            # 2. Read rate limits
            rl_req = json.dumps({"id": "1", "method": "account/rateLimits/read", "params": {}}) + "\n"
            p.stdin.write(rl_req)
            p.stdin.flush()

            rl_data = None
            start = time.time()
            while time.time() - start < 5:
                line = p.stdout.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                    if data.get("id") == "1":
                        rl_data = data.get("result", {}).get("rateLimits", {})
                        break
                except Exception:
                    pass

            p.terminate()

            if not rl_data:
                return None

            primary = rl_data.get("primary", {})
            secondary = rl_data.get("secondary", {})
            plan_type = rl_data.get("planType", "plus")
            limit_reached = rl_data.get("rateLimitReachedType")

            # 5-hour rate limit (primary)
            p_used_pct = float(primary.get("usedPercent", 0))
            p_rem_pct = round(max(0.0, 100.0 - p_used_pct), 1)
            p_reset_ts = primary.get("resetsAt")
            p_reset_str = self._format_reset_time(p_reset_ts, 5 * 3600)

            # 7-day rate limit (secondary)
            s_used_pct = float(secondary.get("usedPercent", 100))
            s_rem_pct = round(max(0.0, 100.0 - s_used_pct), 1)
            s_reset_ts = secondary.get("resetsAt")
            s_reset_str = self._format_reset_time(s_reset_ts, 7 * 24 * 3600)

            tier = plan_type.capitalize() if plan_type else "Plus"

            status = "ok"
            status_text = "app-server 联机"
            if limit_reached or s_rem_pct <= 0:
                status = "warning"
                status_text = "周额度已耗尽"

            short_metric = f"{p_rem_pct}% 剩余 (已用 {int(p_used_pct)}%)"
            long_metric = f"{s_rem_pct}% 剩余 (已用 {int(s_used_pct)}%)"

            return QuotaResult(
                service_id=self.service_id,
                service_name=self.service_name,
                status=status,
                status_text=status_text,
                tier=tier,
                short_term_label="5小时余量",
                short_term_metric=f"{short_metric} · {p_reset_str}",
                short_term_pct=p_rem_pct,
                long_term_label="一周余量",
                long_term_metric=f"{long_metric} · {s_reset_str}",
                long_term_pct=s_rem_pct,
                primary_metric=f"5h: {p_rem_pct}% | 周: {s_rem_pct}%",
                secondary_metric=f"Codex 速率配额 ({tier})",
                percentage=p_rem_pct,
                details=rl_data
            )

        except Exception as e:
            print(f"[Codex] app-server query error: {e}")
            return None

    def _format_reset_time(self, reset_ts: Optional[int], fallback_delta: int) -> str:
        now = time.time()
        if not reset_ts:
            reset_ts = int(now + fallback_delta)

        # If reset_ts is in milliseconds
        if reset_ts > 1e11:
            reset_ts = int(reset_ts / 1000)

        delta_sec = reset_ts - now
        if delta_sec <= 0:
            return "即将重置"

        if delta_sec < 3600:
            return f"约 {int(delta_sec // 60)} 分钟后重置"
        elif delta_sec < 86400:
            return f"约 {round(delta_sec / 3600, 1)} 小时后重置"
        else:
            days = round(delta_sec / 86400, 1)
            target_time_str = time.strftime("%m-%d %H:%M", time.localtime(reset_ts))
            return f"约 {days} 天后重置 ({target_time_str})"

    def _fetch_fallback(self) -> QuotaResult:
        """Fallback status if app-server cannot be queried."""
        return QuotaResult(
            service_id=self.service_id,
            service_name=self.service_name,
            status="warning",
            status_text="等待连接",
            tier="Plus",
            short_term_label="5小时余量",
            short_term_metric="待连接 / 手动",
            short_term_pct=100.0,
            long_term_label="一周余量",
            long_term_metric="待连接 / 手动",
            long_term_pct=0.0,
            primary_metric="待连接",
            secondary_metric="请启动 Codex 或点击授权"
        )

    def trigger_login(self):
        """Invoke codex browser login flow."""
        try:
            subprocess.Popen(["/usr/lib/chatgpt/resources/codex", "login"])
        except Exception as e:
            print(f"[Codex] Failed to trigger codex login: {e}")
            webbrowser.open("https://chatgpt.com")
