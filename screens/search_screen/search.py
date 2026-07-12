import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget
from core.api_client import search_players_by_name, parse_steam_id_input


class SearchScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Токен текущего поиска. Нужен, чтобы если пользователь быстро
        # ввёл новый запрос, ответ на СТАРЫЙ запрос не перезаписал
        # уже актуальный список результатов (гонка потоков).
        self._search_token = 0
        self.search_mode = "nickname"

    def on_kv_post(self, base_widget):
        self.set_search_mode("nickname")

    def open_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def set_search_mode(self, mode):
        """Переключает режим поиска: 'nickname' (через OpenDota) или 'id' (точный ID/ссылка)."""
        self.search_mode = mode

        active_color = (0.22, 0.28, 0.17, 1)
        inactive_color = (0.3, 0.3, 0.3, 1)

        if mode == "nickname":
            self.ids.mode_btn_nickname.md_bg_color = active_color
            self.ids.mode_btn_id.md_bg_color = inactive_color
            self.ids.search_input.hint_text = "Введите никнейм игрока"
        else:
            self.ids.mode_btn_nickname.md_bg_color = inactive_color
            self.ids.mode_btn_id.md_bg_color = active_color
            self.ids.search_input.hint_text = "Steam ID / SteamID64 / ссылка на профиль"

    def start_search(self):
        query = self.ids.search_input.text.strip()
        if not query:
            return

        if self.search_mode == "id":
            direct_id = parse_steam_id_input(query)
            if direct_id:
                self.open_profile(direct_id)
            else:
                self._show_invalid_id_dialog()
            return

        self._search_token += 1
        my_token = self._search_token

        self.ids.loading_spinner.active = True
        self.ids.results_list.clear_widgets()

        threading.Thread(target=self._network_search, args=(query, my_token), daemon=True).start()

    def _network_search(self, query, token):
        players = search_players_by_name(query)
        Clock.schedule_once(lambda dt: self._render_results(players, token), 0)

    def _render_results(self, players, token):
        # Если пользователь уже запустил новый поиск - этот результат устарел, игнорируем
        if token != self._search_token:
            return

        self.ids.loading_spinner.active = False
        self.ids.results_list.clear_widgets()

        if not players:
            self._show_not_found_dialog()
            return

        for p in players:
            account_id = str(p.get("account_id", ""))
            if not account_id:
                continue

            personaname = p.get("personaname") or "Без ника"
            avatar_url = p.get("avatar") or "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"

            secondary_text = f"ID: {account_id}"
            last_match = p.get("last_match_time")
            if last_match:
                # Показываем только дату (без времени), если формат ISO-строка
                last_match_date = str(last_match).split("T")[0].split(" ")[0]
                secondary_text += f" · последний матч: {last_match_date}"

            # Верхняя строка - ник игрока, нижняя - его Steam (Dota) ID
            # и дата последнего матча, чтобы отличать тёзок друг от друга.
            item = TwoLineAvatarListItem(
                text=personaname,
                secondary_text=secondary_text,
                text_color=(1, 1, 1, 1),
                secondary_text_color=(0.6, 0.6, 0.6, 1),
            )
            item.add_widget(ImageLeftWidget(source=avatar_url))
            item.bind(on_release=lambda x, uid=account_id: self.open_profile(uid))
            self.ids.results_list.add_widget(item)

    def _show_not_found_dialog(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="Игрок не найден",
            text=(
                "Совпадений не найдено.\n\n"
                "Учти: поиск по нику ищет только среди игроков, чьи публичные "
                "матчи уже проиндексированы OpenDota. Если игрок недавно "
                "не играл или скрыл профиль, попробуй ввести его точный "
                "числовой Steam ID."
            ),
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    def _show_invalid_id_dialog(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="Не распознано",
            text=(
                "Не удалось распознать ID/ссылку.\n\n"
                "Поддерживаются: голый SteamID (account_id), SteamID64 (17 цифр), "
                "https://steamcommunity.com/profiles/... и "
                "https://steamcommunity.com/id/..."
            ),
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss(),
                )
            ],
        )
        self.dialog.open()

    def open_profile(self, account_id):
        if not account_id:
            return
        profile_screen = self.manager.get_screen("profile")
        profile_screen.load_player_data(str(account_id))
        self.manager.transition.direction = "left"
        self.manager.current = "profile"