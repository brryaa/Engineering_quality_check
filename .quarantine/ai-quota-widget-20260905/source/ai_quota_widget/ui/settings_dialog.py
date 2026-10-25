import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent, config_manager, on_save_callback):
        super().__init__(
            title="偏好设置 & 凭证管理",
            transient_for=parent,
            flags=0
        )
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback

        self.set_default_size(440, 480)
        self.set_modal(True)

        self._build_ui()

    def _build_ui(self):
        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        app_cfg = self.config_manager.get_app_config()

        # 1. General settings frame
        gen_frame = Gtk.Frame(label="通用悬浮窗设置")
        gen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        gen_box.set_margin_top(8)
        gen_box.set_margin_bottom(8)
        gen_box.set_margin_start(12)
        gen_box.set_margin_end(12)

        # Always on top
        self.chk_always_top = Gtk.CheckButton(label="保持窗口置顶 (Always on Top)")
        self.chk_always_top.set_active(app_cfg.get("always_on_top", True))
        gen_box.pack_start(self.chk_always_top, False, False, 0)

        # Refresh interval
        int_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        int_box.pack_start(Gtk.Label(label="自动刷新频率:"), False, False, 0)

        self.combo_interval = Gtk.ComboBoxText()
        intervals = [
            ("60", "1 分钟"),
            ("300", "5 分钟 (推荐)"),
            ("900", "15 分钟"),
            ("1800", "30 分钟"),
            ("0", "仅手动刷新")
        ]
        curr_int = str(app_cfg.get("refresh_interval", 300))
        for key, text in intervals:
            self.combo_interval.append(key, text)
        self.combo_interval.set_active_id(curr_int if curr_int in [k for k, _ in intervals] else "300")
        int_box.pack_start(self.combo_interval, True, True, 0)
        gen_box.pack_start(int_box, False, False, 0)

        gen_frame.add(gen_box)
        box.pack_start(gen_frame, False, False, 0)

        # 2. Codex settings frame
        codex_cfg = self.config_manager.get_service_config("codex")
        codex_frame = Gtk.Frame(label="🤖 Codex (ChatGPT) 授权")
        codex_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        codex_box.set_margin_top(8)
        codex_box.set_margin_bottom(8)
        codex_box.set_margin_start(12)
        codex_box.set_margin_end(12)

        self.chk_codex_app = Gtk.CheckButton(label="优先使用本机已安装 App 现成 API (推荐)")
        self.chk_codex_app.set_active(codex_cfg.get("auth_mode", "app") == "app")
        codex_box.pack_start(self.chk_codex_app, False, False, 0)

        codex_cookie_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        codex_cookie_box.pack_start(Gtk.Label(label="网页凭据:"), False, False, 0)
        self.entry_codex_cookie = Gtk.Entry()
        self.entry_codex_cookie.set_placeholder_text("Session Token 或 Cookie")
        self.entry_codex_cookie.set_text(codex_cfg.get("cookie", "") or codex_cfg.get("access_token", "")[:30] if codex_cfg.get("access_token") else "")
        codex_cookie_box.pack_start(self.entry_codex_cookie, True, True, 0)
        codex_box.pack_start(codex_cookie_box, False, False, 0)

        codex_frame.add(codex_box)
        box.pack_start(codex_frame, False, False, 0)

        # 3. Grok Build settings frame
        grok_cfg = self.config_manager.get_service_config("grok")
        grok_frame = Gtk.Frame(label="⚡ Grok Build 授权")
        grok_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        grok_box.set_margin_top(8)
        grok_box.set_margin_bottom(8)
        grok_box.set_margin_start(12)
        grok_box.set_margin_end(12)

        grok_cookie_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        grok_cookie_box.pack_start(Gtk.Label(label="SSO Cookie:"), False, False, 0)
        self.entry_grok_cookie = Gtk.Entry()
        self.entry_grok_cookie.set_placeholder_text("sso=eyJ0eXAi...")
        self.entry_grok_cookie.set_text(grok_cfg.get("sso_cookie", ""))
        grok_cookie_box.pack_start(self.entry_grok_cookie, True, True, 0)
        grok_box.pack_start(grok_cookie_box, False, False, 0)

        grok_model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        grok_model_box.pack_start(Gtk.Label(label="监控模型:"), False, False, 0)
        self.entry_grok_model = Gtk.Entry()
        self.entry_grok_model.set_text(grok_cfg.get("model_name", "grok-3"))
        grok_model_box.pack_start(self.entry_grok_model, True, True, 0)
        grok_box.pack_start(grok_model_box, False, False, 0)

        grok_frame.add(grok_box)
        box.pack_start(grok_frame, False, False, 0)

        # 4. AGY settings frame
        agy_cfg = self.config_manager.get_service_config("agy")
        agy_frame = Gtk.Frame(label="🚀 AGY (Antigravity) 授权")
        agy_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        agy_box.set_margin_top(8)
        agy_box.set_margin_bottom(8)
        agy_box.set_margin_start(12)
        agy_box.set_margin_end(12)

        agy_key_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        agy_key_box.pack_start(Gtk.Label(label="API Key/Token:"), False, False, 0)
        self.entry_agy_key = Gtk.Entry()
        self.entry_agy_key.set_placeholder_text("可选: 留空则自动读取本机 CLI 配置")
        self.entry_agy_key.set_text(agy_cfg.get("api_key", ""))
        agy_key_box.pack_start(self.entry_agy_key, True, True, 0)
        agy_box.pack_start(agy_key_box, False, False, 0)

        agy_frame.add(agy_box)
        box.pack_start(agy_frame, False, False, 0)

        # Action Buttons
        self.add_button("取消", Gtk.ResponseType.CANCEL)
        save_btn = self.add_button("保存配置", Gtk.ResponseType.OK)
        save_btn.get_style_context().add_class("suggested-action")

        self.connect("response", self._on_response)
        self.show_all()

    def _on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            # Save app config
            new_interval = int(self.combo_interval.get_active_id() or "300")
            always_top = self.chk_always_top.get_active()

            self.config_manager.update_app_config({
                "refresh_interval": new_interval,
                "always_on_top": always_top
            })

            # Save Codex
            use_app = self.chk_codex_app.get_active()
            codex_cookie = self.entry_codex_cookie.get_text().strip()
            codex_updates = {"auth_mode": "app" if use_app else "browser"}
            if codex_cookie:
                codex_updates["cookie"] = codex_cookie
            self.config_manager.update_service_config("codex", codex_updates)

            # Save Grok
            grok_cookie = self.entry_grok_cookie.get_text().strip()
            grok_model = self.entry_grok_model.get_text().strip() or "grok-3"
            grok_updates = {"model_name": grok_model}
            if grok_cookie:
                grok_updates["sso_cookie"] = grok_cookie
                grok_updates["auth_mode"] = "browser"
            self.config_manager.update_service_config("grok", grok_updates)

            # Save AGY
            agy_key = self.entry_agy_key.get_text().strip()
            agy_updates = {}
            if agy_key:
                agy_updates["api_key"] = agy_key
                agy_updates["auth_mode"] = "browser"
            else:
                agy_updates["auth_mode"] = "local"
            self.config_manager.update_service_config("agy", agy_updates)

            self.on_save_callback()

        self.destroy()
