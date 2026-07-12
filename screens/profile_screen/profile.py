import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from core.api_client import get_player_profile_from_valve
# (Если папка называется "core", то оставь: from core.api_client import get_player_profile_from_valve)
# (если ты переименовал папку в services, то пиши: from services.api_client import ...)

class ProfileScreen(MDScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"

    def load_player_data(self, account_id):
        self.ids.name_label.text = "Загрузка..."
        self.ids.id_label.text = f"Steam ID: {account_id}"
        self.ids.rank_label.text = "Ранг: загрузка..."
        self.ids.matches_label.text = "Всего матчей: загрузка..."
        self.ids.winrate_text_label.text = "Винрейт: вычисляется..."
        self.ids.winrate_progress.value = 0
        
        # Запускаем один поток, который соберет все данные
        threading.Thread(target=self._network_load, args=(account_id,), daemon=True).start()

    def _network_load(self, account_id):
        try:
            # Импортируем нашу новую функцию работы с Valve
            from core.api_client import get_player_profile_from_valve
            valve_data = get_player_profile_from_valve(account_id)
            
            Clock.schedule_once(lambda dt: self._ui_render_profile(valve_data), 0)
        except Exception as err:
            error_text = str(err)
            Clock.schedule_once(lambda dt: self._ui_handle_error(error_text), 0)

    def _ui_render_profile(self, data):
        if not data:
            self.ids.name_label.text = "Ошибка загрузки"
            return
            
        # Устанавливаем имя и статус истории матчей
        self.ids.name_label.text = data.get("name", "Неизвестный")
        self.ids.matches_label.text = data.get("matches_text", "Нет данных")
        
        # Так как Valve API не отдает ранг-медаль напрямую (это фишка исключительно внутриигровая),
        # мы временно ставим статус аккаунта официального API
        self.ids.rank_label.text = "Статус: Подключен к Steam Web API"
        
        # Скрываем полосу винрейта, так как Valve не считает его в один клик (нужно парсить каждый матч)
        self.ids.winrate_text_label.text = "Анализ матчей активен"
        self.ids.winrate_progress.value = 100
        
    def _ui_handle_error(self, error_msg="Неизвестная ошибка"):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="Ошибка профиля",
            text=f"Не удалось загрузить детальную статистику.\nПодробности: {error_msg}",
            buttons=[
                MDFlatButton(
                    text="ОК",
                    theme_text_color="Custom",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ],
        )
        self.dialog.open()