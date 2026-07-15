import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineListItem
from kivymd.app import MDApp
from core.api_client import get_player_profile, get_recent_matches
from core.favorites_store import is_favorite, add_favorite, remove_favorite


class ProfileScreen(MDScreen):
    _current_account_id = None
    _current_name = ""
    _current_avatar = ""

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"

    def load_player_data(self, account_id):
        self._current_account_id = str(account_id)
        self._current_name = ""
        self._current_avatar = ""

        self.ids.avatar_image.source = "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"
        self.ids.name_label.text = "Загрузка..."
        self.ids.id_label.text = f"Steam ID: {account_id}"
        self.ids.rank_label.text = "Ранг: загрузка..."
        self.ids.matches_label.text = "Всего матчей: загрузка..."
        self.ids.winrate_text_label.text = "Винрейт: вычисляется..."
        self.ids.winrate_progress.value = 0
        self.ids.top_hero_label.text = "Лучший герой: —"
        self.ids.recent_matches_list.clear_widgets()
        self._update_favorite_button()

        threading.Thread(target=self._network_load, args=(account_id,), daemon=True).start()
        threading.Thread(target=self._network_load_matches, args=(account_id,), daemon=True).start()

    def _network_load(self, account_id):
        try:
            data = get_player_profile(account_id)
            Clock.schedule_once(lambda dt: self._ui_render_profile(data), 0)
        except Exception as err:
            error_text = str(err)
            Clock.schedule_once(lambda dt: self._ui_handle_error(error_text), 0)

    def _network_load_matches(self, account_id):
        matches = get_recent_matches(account_id, limit=5)
        Clock.schedule_once(lambda dt: self._ui_render_matches(matches), 0)

    def _ui_render_profile(self, data):
        if not data:
            self.ids.name_label.text = "Ошибка загрузки"
            return

        self._current_name = data.get("name", "Неизвестный")
        self._current_avatar = data.get("avatar", "")

        self.ids.name_label.text = self._current_name
        if self._current_avatar:
            self.ids.avatar_image.source = self._current_avatar
        self.ids.matches_label.text = data.get("matches_text", "Нет данных")

        source = data.get("source")
        if source == "stratz":
            self.ids.rank_label.text = f"Ранг: {data.get('rank', '—')}"
        else:
            self.ids.rank_label.text = "Ранг: доступен только через STRATZ"

        if "winrate" in data:
            winrate = data["winrate"]
            self.ids.winrate_text_label.text = f"Винрейт: {winrate}%"
            self.ids.winrate_progress.value = winrate
        else:
            self.ids.winrate_text_label.text = "Винрейт: недоступен без STRATZ ключа"
            self.ids.winrate_progress.value = 0

        self.ids.top_hero_label.text = "Лучший герой: доступно только через STRATZ"

        # Аватар уже мог прийти и раньше из данных избранного - обновим кнопку
        # на случай, если это первое сохранение аватара для уже избранного игрока.
        self._update_favorite_button()

    def _ui_render_matches(self, matches):
        self.ids.recent_matches_list.clear_widgets()

        if not matches:
            self.ids.recent_matches_list.add_widget(
                TwoLineListItem(text="Матчи не найдены", secondary_text="STRATZ (premium) или OpenDota недоступны")
            )
            return

        app = MDApp.get_running_app()
        win_color = (0.3, 0.75, 0.35, 1)
        lose_color = (0.8, 0.3, 0.3, 1)

        for m in matches:
            item = TwoLineListItem(
                text=f"{m['result']}  ·  {m['hero_name']}",
                secondary_text=f"KDA: {m['kda']}   ·   {m['duration']}   ·   {m['date']}",
                text_color=win_color if m["won"] else lose_color,
                secondary_text_color=app.secondary_text_color,
            )
            self.ids.recent_matches_list.add_widget(item)

    def toggle_favorite(self):
        if not self._current_account_id:
            return

        if is_favorite(self._current_account_id):
            remove_favorite(self._current_account_id)
        else:
            add_favorite(self._current_account_id, self._current_name, self._current_avatar)

        self._update_favorite_button()

    def _update_favorite_button(self):
        if not self._current_account_id:
            return
        favorited = is_favorite(self._current_account_id)
        self.ids.favorite_button.icon = "star" if favorited else "star-outline"

    def _ui_handle_error(self, error_msg="Неизвестная ошибка"):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        app = MDApp.get_running_app()
        self.dialog = MDDialog(
            title="Ошибка профиля",
            text=f"Не удалось загрузить детальную статистику.\nПодробности: {error_msg}",
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