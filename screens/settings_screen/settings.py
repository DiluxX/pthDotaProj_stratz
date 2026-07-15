from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from config import store


class SettingsScreen(MDScreen):
    def on_pre_enter(self):
        """Вызывается прямо перед открытием экрана: загружаем ключи и текущую тему"""
        data = store.get('app_settings') if store.exists('app_settings') else {}
        self.ids.steam_key_input.text = data.get('api_key', "")
        self.ids.stratz_key_input.text = data.get('stratz_api_key', "")
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

    def save_settings(self):
        steam_key = self.ids.steam_key_input.text.strip()
        stratz_key = self.ids.stratz_key_input.text.strip()

        data = store.get('app_settings') if store.exists('app_settings') else {}
        data['api_key'] = steam_key
        data['stratz_api_key'] = stratz_key
        store.put('app_settings', **data)

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        app = MDApp.get_running_app()
        self.dialog = MDDialog(
            title="Настройки сохранены",
            text="Новая конфигурация успешно записана в память устройства!",
            buttons=[
                MDFlatButton(
                    text="ОК",
                    theme_text_color="Custom",
                    text_color=app.accent_color,
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"