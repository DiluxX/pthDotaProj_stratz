from kivy.properties import ColorProperty
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.lang import Builder

# Импортируем классы логики экранов
from screens.splash_screen.splash import SplashScreen
from screens.search_screen.search import SearchScreen
from screens.profile_screen.profile import ProfileScreen
from screens.settings_screen.settings import SettingsScreen
from screens.favorites_screen.favorites import FavoritesScreen
from screens.heroes_screen.heroes import HeroesScreen

from core.theme_manager import get_saved_theme_mode, resolve_theme


class DotaStatsApp(MDApp):
    # Динамические цвета темы - все .kv-файлы ссылаются на них через `app.xxx`,
    # поэтому при смене темы (apply_theme) интерфейс обновляется автоматически.
    bg_color = ColorProperty((0.09, 0.09, 0.09, 1))
    surface_color = ColorProperty((0.16, 0.16, 0.16, 1))
    accent_color = ColorProperty((0.22, 0.28, 0.17, 1))
    text_color = ColorProperty((1, 1, 1, 1))
    secondary_text_color = ColorProperty((0.62, 0.62, 0.62, 1))

    def build(self):
        # Подгружаем все KV файлы декларативного дизайна
        Builder.load_file("screens/splash_screen/splash.kv")
        Builder.load_file("screens/search_screen/search.kv")
        Builder.load_file("screens/profile_screen/profile.kv")
        Builder.load_file("screens/settings_screen/settings.kv")
        Builder.load_file("screens/favorites_screen/favorites.kv")
        Builder.load_file("screens/heroes_screen/heroes.kv")

        self.apply_theme(get_saved_theme_mode())

        # Настраиваем менеджер окон со слайд-анимациями перехода
        sm = ScreenManager(transition=SlideTransition())

        # Порядок добавления определяет стартовый экран (первый — splash)
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(SearchScreen(name="search"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(FavoritesScreen(name="favorites"))
        sm.add_widget(HeroesScreen(name="heroes"))

        return sm

    def apply_theme(self, mode: str):
        """mode: 'system' | 'purple' | 'light'"""
        palette = resolve_theme(mode)

        self.theme_cls.theme_style = palette["style"]
        self.bg_color = palette["bg"]
        self.surface_color = palette["surface"]
        self.accent_color = palette["accent"]
        self.text_color = palette["text"]
        self.secondary_text_color = palette["secondary_text"]


if __name__ == "__main__":
    DotaStatsApp().run()