from kivymd.uix.screen import MDScreen
from config import store


class SettingsScreen(MDScreen):
    def on_pre_enter(self):
        """Вызывается прямо перед открытием экрана: загружаем ключи из памяти"""
        data = store.get('app_settings') if store.exists('app_settings') else {}
        self.ids.steam_key_input.text = data.get('api_key', "")
        self.ids.stratz_key_input.text = data.get('stratz_api_key', "")

    def save_settings(self):
        steam_key = self.ids.steam_key_input.text.strip()
        stratz_key = self.ids.stratz_key_input.text.strip()

        store.put('app_settings', api_key=steam_key, stratz_api_key=stratz_key)

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="Настройки сохранены",
            text="Новая конфигурация успешно записана в память устройства!",
            buttons=[
                MDFlatButton(
                    text="ОК",
                    theme_text_color="Custom",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"