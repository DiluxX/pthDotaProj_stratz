from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from config import store


class SettingsScreen(MDScreen):
    def on_pre_enter(self):
        """Вызывается прямо перед открытием экрана: загружаем текущую тему"""
        data = store.get('app_settings') if store.exists('app_settings') else {}
        self._highlight_theme_buttons(data.get('app_theme', 'system'))

    def set_theme(self, mode):
        app = MDApp.get_running_app()
        app.apply_theme(mode)

        from core.theme_manager import save_theme_mode
        save_theme_mode(mode)

        self._highlight_theme_buttons(mode)

    def _highlight_theme_buttons(self, mode):
        app = MDApp.get_running_app()
        active = app.accent_color
        inactive = (0.4, 0.4, 0.4, 1)

        self.ids.theme_btn_system.md_bg_color = active if mode == "system" else inactive
        self.ids.theme_btn_purple.md_bg_color = active if mode == "purple" else inactive
        self.ids.theme_btn_light.md_bg_color = active if mode == "light" else inactive

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"