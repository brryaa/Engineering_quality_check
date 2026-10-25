import gi
import os
import threading
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import Dict, List, Callable, Optional, Any
from .card import ServiceCard
from .settings_dialog import SettingsDialog
from ..services.base import QuotaResult

class MiniBarWindow(Gtk.Window):
    """Ultra-compact 28px height floating pill docked to screen edge with zero black area."""
    def __init__(self, on_expand_requested: Callable[[], None]):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("AI Quota Pill")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_role("floating-pill")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)

        self.on_expand_requested = on_expand_requested
        self.get_style_context().add_class("mini-pill-window")

        # Container
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        container.get_style_context().add_class("mini-container")

        self.summary_label = Gtk.Label(label="🤖 --% | 🚀 --% | ⚡ --%")
        self.summary_label.get_style_context().add_class("mini-text")
        self.summary_label.set_tooltip_text("余量规格: 🤖 Codex(5h/周) │ 🚀 AGY(5h/周) │ ⚡ Grok(周)")
        container.pack_start(self.summary_label, True, True, 4)

        self.btn_expand = Gtk.Button(label="▼")
        self.btn_expand.get_style_context().add_class("mini-btn-expand")
        self.btn_expand.connect("clicked", lambda w: self.on_expand_requested())
        container.pack_end(self.btn_expand, False, False, 2)

        # Drag & Click
        event_box = Gtk.EventBox()
        event_box.add(container)
        event_box.connect("button-press-event", self._on_button_press)
        self.add(event_box)

        # Mouse hover to expand
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.connect("enter-notify-event", self._on_enter_notify)

    def _on_enter_notify(self, widget, event):
        self.on_expand_requested()
        return False

    def _on_button_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            if event.y < 28 and event.x < 220:
                self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
                return True
        return False

    def update_summary(self, text: str):
        self.summary_label.set_text(text)


class MainWindow(Gtk.Window):
    def __init__(self, config_manager, auth_server, services: Any):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config_manager = config_manager
        self.auth_server = auth_server
        if isinstance(services, dict):
            self.services_dict = services
            self.services = list(services.values())
        else:
            self.services = services
            self.services_dict = {s.service_id: s for s in services}

        self.cards: Dict[str, ServiceCard] = {}
        self.is_pinned = False
        self._collapse_timer_id = None
        self._last_x = 1000
        self._last_y = 60

        # Paired mini pill window
        self.mini_window = MiniBarWindow(on_expand_requested=self.expand_from_mini)

        self._setup_window()
        self._build_ui()
        self._apply_css()

        # Connect hover leave on main window
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("enter-notify-event", self._on_mouse_enter)
        self.connect("leave-notify-event", self._on_mouse_leave)

        # Initial refresh and timer
        self.show_all()
        self.refresh_all()
        self._setup_timer()

    def _setup_window(self):
        self.set_title("AI Quota Hub")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(False)
        self.set_role("floating-widget")
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)

        screen = Gdk.Screen.get_default()
        if screen:
            screen_w = screen.get_width()
            self._last_x = max(50, screen_w - 365)
            self._last_y = 60
            self.move(self._last_x, self._last_y)

    def _apply_css(self):
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            try:
                provider.load_from_path(css_path)
                screen = Gdk.Screen.get_default()
                Gtk.StyleContext.add_provider_for_screen(
                    screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e:
                print(f"[Window] Error loading CSS: {e}")

    def _build_ui(self):
        self.get_style_context().add_class("floating-window")

        event_box = Gtk.EventBox()
        event_box.connect("button-press-event", self._on_window_drag_press)

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.root_box.get_style_context().add_class("main-container")
        event_box.add(self.root_box)
        self.add(event_box)

        # Header bar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.get_style_context().add_class("header-bar")

        title = Gtk.Label(label="🔮 AI 算力余量")
        title.get_style_context().add_class("app-title")
        header.pack_start(title, False, False, 0)

        # Header Actions
        self.btn_refresh = Gtk.Button(label="🔄")
        self.btn_refresh.set_tooltip_text("刷新全部")
        self.btn_refresh.get_style_context().add_class("header-btn")
        self.btn_refresh.connect("clicked", lambda w: self.refresh_all())
        header.pack_end(self.btn_refresh, False, False, 0)

        self.btn_collapse = Gtk.Button(label="▲")
        self.btn_collapse.set_tooltip_text("折叠贴边 (鼠标移入展开)")
        self.btn_collapse.get_style_context().add_class("header-btn")
        self.btn_collapse.connect("clicked", lambda w: self.collapse_to_mini())
        header.pack_end(self.btn_collapse, False, False, 0)

        self.btn_pin = Gtk.Button(label="📌")
        self.btn_pin.set_tooltip_text("固定常驻 (防止鼠标移出自动收起)")
        self.btn_pin.get_style_context().add_class("header-btn")
        self.btn_pin.connect("clicked", self._on_toggle_pin)
        header.pack_end(self.btn_pin, False, False, 0)

        btn_settings = Gtk.Button(label="⚙️")
        btn_settings.set_tooltip_text("设置与凭证")
        btn_settings.get_style_context().add_class("header-btn")
        btn_settings.connect("clicked", self._on_settings_clicked)
        header.pack_end(btn_settings, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_tooltip_text("关闭退出")
        btn_close.get_style_context().add_class("header-btn")
        btn_close.get_style_context().add_class("header-btn-close")
        btn_close.connect("clicked", lambda w: Gtk.main_quit())
        header.pack_end(btn_close, False, False, 0)

        self.root_box.pack_start(header, False, False, 0)

        # Service cards container
        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for s in self.services:
            card = ServiceCard(s, self.auth_server, self.refresh_service)
            self.cards[s.service_id] = card
            self.cards_box.pack_start(card, False, False, 0)

        self.root_box.pack_start(self.cards_box, True, True, 0)

    def _setup_timer(self):
        refresh_sec = self.config_manager.get("ui.refresh_interval_sec", 300)
        print(f"[Window] Auto-refresh timer configured: {refresh_sec}s")
        GLib.timeout_add_seconds(refresh_sec, self._on_timer_tick)

    def _on_timer_tick(self):
        self.refresh_all()
        return True

    def refresh_all(self):
        for sid in self.services_dict:
            self.refresh_service(sid)

    def refresh_service(self, service_id: str):
        service = self.services_dict.get(service_id)
        if not service:
            return

        def _worker():
            try:
                res = service.fetch_quota()
                GLib.idle_add(self._on_quota_fetched, res)
            except Exception as e:
                print(f"[Window] Error refreshing {service_id}: {e}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_quota_fetched(self, result: QuotaResult):
        if result.service_id in self.cards:
            self.cards[result.service_id].update_data(result)
            self._update_mini_summary()

    def _update_mini_summary(self):
        codex_card = self.cards.get("codex")
        agy_card = self.cards.get("agy")
        grok_card = self.cards.get("grok")

        parts = []
        if codex_card:
            c_5h = int(codex_card.progress_bar_short.get_fraction() * 100)
            c_1w = int(codex_card.progress_bar_long.get_fraction() * 100)
            parts.append(f"🤖 {c_5h}%/{c_1w}%")

        if agy_card:
            a_5h = int(agy_card.progress_bar_short.get_fraction() * 100)
            a_1w = int(agy_card.progress_bar_long.get_fraction() * 100)
            parts.append(f"🚀 {a_5h}%/{a_1w}%")

        if grok_card:
            g_1w = int(grok_card.progress_bar_long.get_fraction() * 100)
            parts.append(f"⚡ {g_1w}%")

        summary = " │ ".join(parts)
        self.mini_window.update_summary(summary)

    def _on_window_drag_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        return False

    def _on_mouse_enter(self, widget, event):
        if self._collapse_timer_id is not None:
            GLib.source_remove(self._collapse_timer_id)
            self._collapse_timer_id = None
        return False

    def _on_mouse_leave(self, widget, event):
        if not self.is_pinned:
            if self._collapse_timer_id is None:
                self._collapse_timer_id = GLib.timeout_add(700, self._auto_collapse_callback)
        return False

    def _auto_collapse_callback(self):
        self._collapse_timer_id = None
        if not self.is_pinned and self.is_visible():
            self.collapse_to_mini()
        return False

    def _on_toggle_pin(self, widget):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.btn_pin.set_label("📍")
            self.btn_pin.set_tooltip_text("已固定常驻 (点击取消固定)")
            if self._collapse_timer_id is not None:
                GLib.source_remove(self._collapse_timer_id)
                self._collapse_timer_id = None
        else:
            self.btn_pin.set_label("📌")
            self.btn_pin.set_tooltip_text("固定常驻 (防止鼠标移出自动收起)")

    def collapse_to_mini(self):
        """Switch to clean 28px mini bar window."""
        self._last_x, self._last_y = self.get_position()
        self.hide()

        screen = Gdk.Screen.get_default()
        screen_w = screen.get_width() if screen else 1360
        pill_x = max(10, screen_w - 325)

        self.mini_window.move(pill_x, self._last_y)
        self.mini_window.show_all()

    def expand_from_mini(self):
        """Expand from mini bar back to full cards window."""
        if self._collapse_timer_id is not None:
            GLib.source_remove(self._collapse_timer_id)
            self._collapse_timer_id = None

        m_x, m_y = self.mini_window.get_position()
        self.mini_window.hide()

        screen = Gdk.Screen.get_default()
        screen_w = screen.get_width() if screen else 1360
        full_x = max(20, screen_w - 365)

        self.move(full_x, m_y)
        self.show_all()

    def _on_settings_clicked(self, widget):
        dialog = SettingsDialog(self, self.config_manager)
        dialog.run()
        dialog.destroy()


# Compatibility alias
FloatingWindow = MainWindow
