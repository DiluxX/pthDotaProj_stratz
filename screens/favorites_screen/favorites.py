from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarIconListItem, ImageLeftWidget, IconRightWidget
from kivymd.app import MDApp
from core.favorites_store import get_favorites, remove_favorite


class FavoritesScreen(MDScreen):

    def on_pre_enter(self):
        self.refresh_list()

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"

    def refresh_list(self):
        app = MDApp.get_running_app()
        self.ids.favorites_list.clear_widgets()
        favorites = get_favorites()

        if not favorites:
            self.ids.empty_label.text = "Список избранного пуст.\nДобавь игроков со страницы профиля."
            self.ids.empty_label.opacity = 1
            return

        self.ids.empty_label.opacity = 0

        for p in favorites:
            account_id = p.get("account_id")
            item = TwoLineAvatarIconListItem(
                text=p.get("personaname", f"ID {account_id}"),
                secondary_text=f"ID: {account_id}",
                text_color=app.text_color,
                secondary_text_color=app.secondary_text_color,
            )
            item.add_widget(ImageLeftWidget(source=p.get("avatar", "")))

            remove_icon = IconRightWidget(icon="delete")
            remove_icon.bind(on_release=lambda x, uid=account_id: self._remove(uid))
            item.add_widget(remove_icon)

            item.bind(on_release=lambda x, uid=account_id: self.open_profile(uid))
            self.ids.favorites_list.add_widget(item)

    def _remove(self, account_id):
        remove_favorite(account_id)
        self.refresh_list()

    def open_profile(self, account_id):
        profile_screen = self.manager.get_screen("profile")
        profile_screen.load_player_data(str(account_id))
        self.manager.transition.direction = "left"
        self.manager.current = "profile"