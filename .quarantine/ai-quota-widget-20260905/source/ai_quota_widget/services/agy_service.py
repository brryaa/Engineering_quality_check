import os
import json
import time
import datetime
from typing import Dict, Any, Optional, Tuple
from .base import BaseService, QuotaResult

class AgyService(BaseService):
    def __init__(self, config_manager):
        super().__init__("agy", "AGY (Antigravity)", config_manager)

    def fetch_quota(self) -> QuotaResult:
        cfg = self.get_auth_info()
        auth_mode = cfg.get("auth_mode", "local")

        return self._fetch_antigravity_quota()

    def _fetch_antigravity_quota(self) -> QuotaResult:
        """Fetch Antigravity 5-hour sprint quota and 7-day weekly baseline quota."""
        settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
        model_name = "Gemini 3.8 Flash (High)"
        is_local_configured = False

        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                model_name = sdata.get("model", model_name)
                is_local_configured = True
            except Exception:
                pass

        # Check presence locks
        presence_dir = os.path.expanduser("~/.gemini/antigravity-cli/presence")
        is_active = False
        if os.path.exists(presence_dir):
            locks = [f for f in os.listdir(presence_dir) if f.endswith(".lock")]
            is_active = len(locks) > 0

        # Calculate 5-hour and 7-day usage from local conversation history
        used_5h, used_week, reset_5h_ts, reset_week_ts = self._scan_recent_usage()

        # Quota caps for Google AI Pro / Standard Tier
        # 5-hour sprint capacity: 150 prompt/tool turns
        # 7-day weekly baseline hard cap: 800 prompt/tool turns
        cap_5h = 150
        cap_week = 800

        used_5h_pct = min(100.0, round((used_5h / cap_5h) * 100.0, 1))
        rem_5h_pct = round(max(0.0, 100.0 - used_5h_pct), 1)

        used_week_pct = min(100.0, round((used_week / cap_week) * 100.0, 1))
        rem_week_pct = round(max(0.0, 100.0 - used_week_pct), 1)

        now = time.time()
        # Format 5h reset
        if reset_5h_ts and reset_5h_ts > now:
            delta_h = round((reset_5h_ts - now) / 3600.0, 1)
            reset_5h_str = f"约 {delta_h} 小时后重置"
        else:
            reset_5h_str = "5小时滚动重置"

        # Format week reset
        if reset_week_ts and reset_week_ts > now:
            dt = datetime.datetime.fromtimestamp(reset_week_ts)
            delta_d = round((reset_week_ts - now) / 86400.0, 1)
            reset_week_str = f"约 {delta_d} 天后重置 ({dt.strftime('%m-%d %H:%M')})"
        else:
            reset_week_str = "周度重置周期"

        tier = "Google AI Pro" if "Pro" in model_name else "Standard Tier"
        status = "ok" if is_local_configured else "warning"
        status_text = "CLI 会话活跃" if is_active else "联机就绪"

        if rem_week_pct <= 5.0 or rem_5h_pct <= 5.0:
            status = "error"
            status_text = "额度告警"
        elif rem_week_pct <= 20.0 or rem_5h_pct <= 20.0:
            status = "warning"
            status_text = "额度消耗过半"

        return QuotaResult(
            service_id=self.service_id,
            service_name=self.service_name,
            status=status,
            status_text=status_text,
            tier=tier,
            has_short_term=True,
            short_term_label="5小时余量",
            short_term_metric=f"{rem_5h_pct}% 剩余 (已用 {used_5h_pct}%) · {reset_5h_str}",
            short_term_pct=rem_5h_pct,
            long_term_label="一周余量",
            long_term_metric=f"{rem_week_pct}% 剩余 (已用 {used_week_pct}%) · {reset_week_str}",
            long_term_pct=rem_week_pct,
            primary_metric=f"5h: {rem_5h_pct}% | 周: {rem_week_pct}%",
            secondary_metric=f"模型: {model_name}",
            percentage=rem_5h_pct,
            details={
                "model": model_name,
                "used_5h": used_5h,
                "used_week": used_week,
                "is_active": is_active
            }
        )

    def _scan_recent_usage(self) -> Tuple[int, int, Optional[float], Optional[float]]:
        history_path = os.path.expanduser("~/.gemini/antigravity-cli/history.jsonl")
        now = time.time()
        five_h_ago = now - 5 * 3600
        one_w_ago = now - 7 * 24 * 3600

        used_5h = 0
        used_week = 0
        earliest_5h = None
        earliest_week = None

        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        item = json.loads(line)
                        ts = item.get("timestamp")
                        if not ts:
                            continue
                        if isinstance(ts, str):
                            import datetime
                            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            ts = dt.timestamp()
                        elif ts > 1e11:
                            ts = ts / 1000.0

                        if ts >= one_w_ago:
                            used_week += 1
                            if earliest_week is None or ts < earliest_week:
                                earliest_week = ts

                        if ts >= five_h_ago:
                            used_5h += 1
                            if earliest_5h is None or ts < earliest_5h:
                                earliest_5h = ts
            except Exception as e:
                print(f"[AGY] Scan warning: {e}")

        reset_5h_ts = (earliest_5h + 5 * 3600) if earliest_5h else (now + 5 * 3600)
        reset_week_ts = (earliest_week + 7 * 86400) if earliest_week else (now + 7 * 86400)

        return used_5h, used_week, reset_5h_ts, reset_week_ts
