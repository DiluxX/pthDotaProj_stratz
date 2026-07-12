from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from config import store

class SettingsScreen(MDScreen):
    def on_pre_enter(self):
        """Вызывается прямо перед открытием экрана: загружаем ключ из памяти"""
        try:
            saved_key = store.get('app_settings')['api_key']
            self.ids.api_key_input.text = saved_key
        except KeyError:
            self.ids.api_key_input.text = ""

    def save_settings(self):
        # Твой текущий код сохранения ключа в store (оставляем как есть)
        api_key = self.ids.api_key_input.text.strip()
        from config import store
        store.put('app_settings', api_key=api_key)
        
        # Вместо капризного Snackbar вызываем железобетонный MDDialog
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="Настройки сохранены",
            text="Новая конфигурация успешно записана в память устройства!",
            buttons=[
                MDFlatButton(
                    text="ОК",
                    theme_text_color="Custom",
                    text_color=(0.22, 0.28, 0.17, 1), # Наш фирменный оливковый
                    on_release=lambda x: self.dialog.dismiss()
                )
            ],
        )
        self.dialog.open()
        
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"
        
        """9883415E836E9431360FC67950FA60B5"""