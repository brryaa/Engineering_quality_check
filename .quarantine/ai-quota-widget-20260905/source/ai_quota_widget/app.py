import signal
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from .config import ConfigManager
from .auth_server import AuthServer
from .services import CodexService, AgyService, GrokService
from .ui import FloatingWindow

class Application:
    def __init__(self):
        self.config_manager = ConfigManager()

        # Initialize Services
        self.services = {
            "codex": CodexService(self.config_manager),
            "agy": AgyService(self.config_manager),
            "grok": GrokService(self.config_manager)
        }

        # Initialize Browser Auth Server
        self.auth_server = AuthServer(
            config_manager=self.config_manager,
            on_auth_callback=self._on_browser_auth_received
        )
        self.auth_server.start()

        # Initialize Floating Window
        self.window = FloatingWindow(
            config_manager=self.config_manager,
            auth_server=self.auth_server,
            services=self.services
        )

        # Handle SIGINT and SIGTERM gracefully
        signal.signal(signal.SIGINT, lambda *_: self.quit())
        signal.signal(signal.SIGTERM, lambda *_: self.quit())

    def _on_browser_auth_received(self, service_id: str):
        print(f"[Application] Browser auth callback for {service_id}, triggering refresh...")
        GLib.idle_add(self.window.refresh_service, service_id)

    def run(self):
        print("[Application] Starting GTK main loop...")
        Gtk.main()

    def quit(self):
        print("[Application] Shutting down...")
        if self.auth_server:
            self.auth_server.stop()
        Gtk.main_quit()
