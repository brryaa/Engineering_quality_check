import gi
import webbrowser
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Callable, Optional
from ..services.base import QuotaResult

class ServiceCard(Gtk.Box):
    def __init__(self, service, auth_server, on_refresh_requested: Callable[[str], None]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.service = service
        self.auth_server = auth_server
        self.on_refresh_requested = on_refresh_requested

        self.get_style_context().add_class("service-card")

        self._build_ui()

    def _build_ui(self):
        # 1. Top row: Icon + Name + Tier Badge + Status
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        icons = {
            "codex": "🤖",
            "agy": "🚀",
            "grok": "⚡"
        }
        icon_str = icons.get(self.service.service_id, "💡")
        self.icon_label = Gtk.Label(label=icon_str)
        top_box.pack_start(self.icon_label, False, False, 0)

        self.title_label = Gtk.Label(label=self.service.service_name)
        self.title_label.get_style_context().add_class("card-title")
        self.title_label.set_xalign(0)
        top_box.pack_start(self.title_label, False, False, 0)

        self.tier_badge = Gtk.Label(label="--")
        self.tier_badge.get_style_context().add_class("tier-badge")
        self.tier_badge.get_style_context().add_class(f"tier-badge-{self.service.service_id}")
        top_box.pack_start(self.tier_badge, False, False, 2)

        self.status_label = Gtk.Label(label="准备中...")
        self.status_label.get_style_context().add_class("status-label")
        self.status_label.set_xalign(1)
        top_box.pack_end(self.status_label, True, True, 0)

        self.pack_start(top_box, False, False, 0)

        # 2. Metric 1: Short-term Quota (5小时余量)
        self.m1_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.m1_label = Gtk.Label(label="5小时余量")
        self.m1_label.get_style_context().add_class("metric-name")
        self.m1_label.set_xalign(0)
        self.m1_header.pack_start(self.m1_label, False, False, 0)

        self.m1_val = Gtk.Label(label="--")
        self.m1_val.get_style_context().add_class("metric-value")
        self.m1_val.set_xalign(1)
        self.m1_header.pack_end(self.m1_val, True, True, 0)
        self.pack_start(self.m1_header, False, False, 0)

        self.progress_bar_short = Gtk.ProgressBar()
        self.progress_bar_short.get_style_context().add_class("progress-short")
        self.progress_bar_short.set_fraction(1.0)
        self.pack_start(self.progress_bar_short, False, False, 1)

        # 3. Metric 2: Long-term Quota (一周余量)
        self.m2_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.m2_header.set_margin_top(2)
        self.m2_label = Gtk.Label(label="一周余量")
        self.m2_label.get_style_context().add_class("metric-name")
        self.m2_label.set_xalign(0)
        self.m2_header.pack_start(self.m2_label, False, False, 0)

        self.m2_val = Gtk.Label(label="--")
        self.m2_val.get_style_context().add_class("metric-value")
        self.m2_val.set_xalign(1)
        self.m2_header.pack_end(self.m2_val, True, True, 0)
        self.pack_start(self.m2_header, False, False, 0)

        self.progress_bar_long = Gtk.ProgressBar()
        self.progress_bar_long.get_style_context().add_class("progress-long")
        self.progress_bar_long.set_fraction(1.0)
        self.pack_start(self.progress_bar_long, False, False, 1)

        # 4. Secondary Info + Time
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        info_box.set_margin_top(2)
        self.secondary_metric_label = Gtk.Label(label="--")
        self.secondary_metric_label.get_style_context().add_class("secondary-metric")
        self.secondary_metric_label.set_xalign(0)
        info_box.pack_start(self.secondary_metric_label, True, True, 0)

        self.time_label = Gtk.Label(label="--:--:--")
        self.time_label.get_style_context().add_class("secondary-metric")
        self.time_label.set_xalign(1)
        info_box.pack_end(self.time_label, False, False, 0)

        self.pack_start(info_box, False, False, 0)

        # 5. Buttons Row
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_box.set_margin_top(4)

        # Refresh button
        self.btn_refresh = Gtk.Button(label="🔄 刷新")
        self.btn_refresh.get_style_context().add_class("action-btn")
        self.btn_refresh.connect("clicked", self._on_refresh_clicked)
        btn_box.pack_start(self.btn_refresh, False, False, 0)

        # Browser auth button
        self.btn_browser_auth = Gtk.Button(label="🌐 浏览器授权")
        self.btn_browser_auth.get_style_context().add_class("action-btn")
        self.btn_browser_auth.get_style_context().add_class("action-btn-primary")
        self.btn_browser_auth.connect("clicked", self._on_browser_auth_clicked)
        btn_box.pack_start(self.btn_browser_auth, False, False, 0)

        # Local sync button
        if self.service.service_id == "codex":
            self.btn_local_sync = Gtk.Button(label="💻 app-server")
            self.btn_local_sync.set_tooltip_text("从已安装的 Codex CLI 本地 app-server 实时获取配额")
            self.btn_local_sync.get_style_context().add_class("action-btn")
            self.btn_local_sync.connect("clicked", self._on_codex_local_sync)
            btn_box.pack_start(self.btn_local_sync, True, True, 0)
        elif self.service.service_id == "grok":
            self.btn_local_sync = Gtk.Button(label="💻 本机凭据")
            self.btn_local_sync.set_tooltip_text("读取本机环境中的 Grok 凭据配置")
            self.btn_local_sync.get_style_context().add_class("action-btn")
            self.btn_local_sync.connect("clicked", self._on_grok_local_sync)
            btn_box.pack_start(self.btn_local_sync, True, True, 0)
        elif self.service.service_id == "agy":
            self.btn_local_sync = Gtk.Button(label="💻 本机CLI")
            self.btn_local_sync.set_tooltip_text("同步本机 Antigravity CLI 配置")
            self.btn_local_sync.get_style_context().add_class("action-btn")
            self.btn_local_sync.connect("clicked", self._on_agy_local_sync)
            btn_box.pack_start(self.btn_local_sync, True, True, 0)

        self.pack_start(btn_box, False, False, 0)

    def update_data(self, result: QuotaResult):
        self.tier_badge.set_text(result.tier or "Standard")
        self.status_label.set_text(result.status_text)
        self.secondary_metric_label.set_text(result.secondary_metric)
        self.time_label.set_text(result.formatted_time)

        # Check if short-term quota exists (e.g. Grok Build only has weekly)
        if result.has_short_term:
            self.m1_header.show()
            self.progress_bar_short.show()
            self.m1_label.set_text(result.short_term_label)
            self.m1_val.set_text(result.short_term_metric)
            frac1 = max(0.0, min(1.0, result.short_term_pct / 100.0))
            self.progress_bar_short.set_fraction(frac1)

            ctx1 = self.progress_bar_short.get_style_context()
            ctx1.remove_class("progress-warning")
            ctx1.remove_class("progress-danger")
            if result.short_term_pct <= 20.0:
                ctx1.add_class("progress-danger")
            elif result.short_term_pct <= 50.0:
                ctx1.add_class("progress-warning")
        else:
            self.m1_header.hide()
            self.progress_bar_short.hide()

        # Update metric 2 (Long term: Weekly)
        self.m2_label.set_text(result.long_term_label)
        self.m2_val.set_text(result.long_term_metric)
        frac2 = max(0.0, min(1.0, result.long_term_pct / 100.0))
        self.progress_bar_long.set_fraction(frac2)

        ctx2 = self.progress_bar_long.get_style_context()
        ctx2.remove_class("progress-warning")
        ctx2.remove_class("progress-danger")
        if result.long_term_pct <= 20.0:
            ctx2.add_class("progress-danger")
        elif result.long_term_pct <= 50.0:
            ctx2.add_class("progress-warning")

    def _on_refresh_clicked(self, widget):
        self.status_label.set_text("刷新中...")
        self.on_refresh_requested(self.service.service_id)

    def _on_browser_auth_clicked(self, widget):
        if self.service.service_id == "codex" and hasattr(self.service, "trigger_login"):
            print("[Card] Invoking codex login browser flow...")
            self.service.trigger_login()
        elif self.service.service_id == "grok":
            url = "https://grok.com"
            try:
                webbrowser.open(url)
            except Exception:
                pass
        else:
            url = self.auth_server.get_auth_url(self.service.service_id)
            print(f"[Card] Opening browser authorization: {url}")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[Card] Failed opening browser: {e}")

    def _on_codex_local_sync(self, widget):
        self.status_label.set_text("查询 app-server...")
        self.on_refresh_requested("codex")

    def _on_grok_local_sync(self, widget):
        self.status_label.set_text("读取 Grok 凭据...")
        self.on_refresh_requested("grok")

    def _on_agy_local_sync(self, widget):
        self.status_label.set_text("同步 AGY 速率...")
        self.on_refresh_requested("agy")
