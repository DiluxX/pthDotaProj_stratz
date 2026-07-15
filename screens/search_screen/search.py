from kivymd.uix.screen import MDScreen
from core.api_client import parse_steam_id_input


class SearchScreen(MDScreen):

    def open_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def open_favorites(self):
        self.manager.transition.direction = "left"
        self.manager.current = "favorites"

    def open_heroes(self):
        self.manager.transition.direction = "left"
        self.manager.current = "heroes"

    def start_search(self):
        query = self.ids.search_input.text.strip()
        if not query:
            return

        account_id = parse_steam_id_input(query)
        if account_id:
            self.open_profile(account_id)
        else:
            self._show_invalid_id_dialog()

    def _show_invalid_id_dialog(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        from kivymd.app import MDApp

        app = MDApp.get_running_app()
        self.dialog = MDDialog(
            title="Не распознано",
            text=(
                "Не удалось распознать ID/ссылку.\n\n"
                "Поддерживаются: голый SteamID (account_id), SteamID64 (17 цифр), "
                "https://steamcommunity.com/profiles/..., "
                "https://steamcommunity.com/id/... и просто короткое vanity-имя "
                "из такой ссылки."
            ),
            buttons=[
                MDFlatButton(
                    text="ПОНЯТНО",
                    text_color=app.accent_color,
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