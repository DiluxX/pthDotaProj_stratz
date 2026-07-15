import threading
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget
from kivymd.app import MDApp
from core.api_client import get_hero_meta_stats


class HeroesScreen(MDScreen):
    _loaded = False

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "search"

    def on_pre_enter(self):
        if self._loaded:
            return
        self.ids.status_label.text = "Загрузка статистики героев..."
        self.ids.status_label.opacity = 1
        threading.Thread(target=self._network_load, daemon=True).start()

    def _network_load(self):
        try:
            heroes = get_hero_meta_stats()
            Clock.schedule_once(lambda dt: self._render(heroes), 0)
        except Exception as e:
            error_text = str(e)
            Clock.schedule_once(lambda dt: self._show_error(error_text), 0)

    def _show_error(self, msg):
        self.ids.status_label.text = f"Не удалось загрузить героев: {msg}"

    def _render(self, heroes):
        self._loaded = True
        self.ids.status_label.opacity = 0
        self.ids.meta_list.clear_widgets()
        self.ids.regular_list.clear_widgets()

        app = MDApp.get_running_app()
        meta_color = (0.3, 0.75, 0.35, 1)

        meta_heroes = [h for h in heroes if h["is_meta"]]
        regular_heroes = [h for h in heroes if not h["is_meta"]]

        self.ids.meta_header.text = f"Мета (винрейт > 51%) — {len(meta_heroes)}"
        self.ids.regular_header.text = f"Обычные герои — {len(regular_heroes)}"

        for h in meta_heroes:
            self.ids.meta_list.add_widget(self._build_item(h, app, meta_color))

        for h in regular_heroes:
            self.ids.regular_list.add_widget(self._build_item(h, app, app.text_color))

    def _build_item(self, h, app, winrate_color):
        item = TwoLineAvatarListItem(
            text=h["name"],
            secondary_text=f"Винрейт: {h['winrate']}%  ·  Пиков: {h['picks']}",
            text_color=app.text_color,
            secondary_text_color=winrate_color,
        )
        item.add_widget(ImageLeftWidget(source=h["image"]))
        return item