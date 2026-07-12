import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineListItem
from kivymd.uix.snackbar import Snackbar
from core.api_client import search_players_by_name

class SearchScreen(MDScreen):
    def open_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def start_search(self):
        query = self.ids.search_input.text.strip()
        if not query:
            return

        if query.isdigit():
            self.open_profile(query)
            return

        self.ids.loading_spinner.active = True
        self.ids.results_list.clear_widgets()
        
        import threading
        threading.Thread(target=self._network_hybrid_search, args=(query,), daemon=True).start()

    def _network_hybrid_search(self, query):
        from core.api_client import search_players_by_name
        from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget
        
        # Запускаем наш новый независимый поиск напрямую через Steam
        players = search_players_by_name(query)
        
        if players:
            def render():
                self.ids.loading_spinner.active = False
                for p in players:
                    account_id = str(p.get("account_id", ""))
                    if not account_id: continue
                    item = TwoLineAvatarListItem(
                        text=str(p.get("personaname", "Без ника")),
                        secondary_text=f"Steam ID: {account_id}",
                        text_color=(1, 1, 1, 1)
                    )
                    avatar = p.get("avatar", "https://steamloopback.host/images/default_avatar.jpg")
                    item.add_widget(ImageLeftWidget(source=avatar))
                    item.bind(on_release=lambda x, uid=account_id: self.open_profile(uid))
                    self.ids.results_list.add_widget(item)
            Clock.schedule_once(lambda dt: render(), 0)
        else:
            # Если даже поиск Steam ничего не выдал (например, нет интернета)
            Clock.schedule_once(lambda dt: self._ui_handle_vanity_error(), 0)

    def _ui_close_spinner_and_open(self, account_id):
        self.ids.loading_spinner.active = False
        self.open_profile(account_id)

    def _ui_handle_vanity_error(self):
        self.ids.loading_spinner.active = False
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        self.dialog = MDDialog(
            title="Игрок не найден",
            text="Не удалось распознать Steam ID. Пожалуйста, введите точный цифровой ID или вашу персональную ссылку (Vanity URL).",
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ],
        )
        self.dialog.open()

    def _network_search(self, query):
        try:
            players = search_players_by_name(query)
            Clock.schedule_once(lambda dt: self._ui_render_results(players), 0)
        except Exception as err:
            # 1. Сразу же превращаем исключение в обычный безопасный текст
            error_text = str(err)
            # 2. Передаем именно error_text БЕЗ использования буквы 'e'
            Clock.schedule_once(lambda dt: self._ui_handle_error(error_text), 0)
            
    def _ui_render_results(self, players):
        self.ids.loading_spinner.active = False
        self.ids.results_list.clear_widgets()
        
        if not players:
            from kivymd.uix.dialog import MDDialog
            from kivymd.uix.button import MDFlatButton
            self.dialog = MDDialog(
                title="Поиск",
                text="Игроки с таким ником не найдены.",
                buttons=[MDFlatButton(text="ОК", text_color=(0.22, 0.28, 0.17, 1), on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()
            return

        # Импортируем элементы списка KivyMD
        from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget

        for p in players:
            account_id = str(p.get("account_id", ""))
            if not account_id:
                continue
                
            # Создаем элемент списка: верхняя строка — ник, нижняя — его ID
            item = TwoLineAvatarListItem(
                text=str(p.get("personaname", "Без ника")),
                secondary_text=f"Steam ID: {account_id}",
                text_color=(1, 1, 1, 1),
                secondary_text_color=(0.6, 0.6, 0.6, 1)
            )
            
            # Добавляем аватарку игрока слева
            avatar_url = p.get("avatar", "https://steamloopback.host/images/default_avatar.jpg")
            avatar_widget = ImageLeftWidget(source=avatar_url)
            item.add_widget(avatar_widget)
            
            # Привязываем клик на игрока: открываем экран профиля по его ID
            item.bind(on_release=lambda x, uid=account_id: self.open_profile(uid))
            
            # Добавляем готовую карточку в наш список на экране
            self.ids.results_list.add_widget(item)
            
    def _ui_handle_error(self, error_msg):
        self.ids.loading_spinner.active = False
        
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        # Проверяем, если ли слово "timeout" в ошибке
        if "timeout" in error_msg.lower():
            title_text = "Сервер поиска перегружен"
            body_text = (
                "OpenDota не успела ответить на поиск по нику.\n\n"
                "💡 **Лайфхак**: Введите в поле поиска числовой **Steam ID** (например, 908706301). "
                "Поиск по ID работает мгновенно и без перегрузок!"
            )
        else:
            title_text = "Ошибка соединения"
            body_text = f"Не удалось получить данные.\nПодробности: {error_msg}"

        self.dialog = MDDialog(
            title=title_text,
            text=body_text,
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    theme_text_color="Custom",
                    text_color=(0.22, 0.28, 0.17, 1),
                    on_release=lambda x: self.dialog.dismiss()
                )
            ],
        )
        self.dialog.open()

    def open_profile(self, account_id):
        if not account_id: return
        profile_screen = self.manager.get_screen("profile")
        profile_screen.load_player_data(str(account_id))
        self.manager.transition.direction = "left"
        self.manager.current = "profile"