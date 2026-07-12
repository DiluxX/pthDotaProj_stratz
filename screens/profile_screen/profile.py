import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from core.api_client import get_player_profile


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
        self.ids.top_hero_label.text = "Лучший герой: —"

        threading.Thread(target=self._network_load, args=(account_id,), daemon=True).start()

    def _network_load(self, account_id):
        try:
            data = get_player_profile(account_id)
            Clock.schedule_once(lambda dt: self._ui_render_profile(data), 0)
        except Exception as err:
            error_text = str(err)
            Clock.schedule_once(lambda dt: self._ui_handle_error(error_text), 0)

    def _ui_render_profile(self, data):
        if not data:
            self.ids.name_label.text = "Ошибка загрузки"
            return

        self.ids.name_label.text = data.get("name", "Неизвестный")
        self.ids.matches_label.text = data.get("matches_text", "Нет данных")

        source = data.get("source")
        if source == "stratz":
            self.ids.rank_label.text = "Источник: STRATZ (свежие данные)"
        else:
            self.ids.rank_label.text = "Источник: Steam Web API"

        if "winrate" in data:
            winrate = data["winrate"]
            self.ids.winrate_text_label.text = f"Винрейт: {winrate}%"
            self.ids.winrate_progress.value = winrate
        else:
            # Valve API не отдаёт готовый винрейт - его пришлось бы считать
            # по каждому матчу отдельно, что уже сделано в STRATZ-ветке.
            self.ids.winrate_text_label.text = "Винрейт: недоступен без STRATZ ключа"
            self.ids.winrate_progress.value = 0

        self.ids.top_hero_label.text = "Лучший герой: доступно только через STRATZ"

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
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()