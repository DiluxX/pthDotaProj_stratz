from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.lang import Builder

# Импортируем классы логики экранов
from screens.splash_screen.splash import SplashScreen
from screens.search_screen.search import SearchScreen
from screens.profile_screen.profile import ProfileScreen
from screens.settings_screen.settings import SettingsScreen

class DotaStatsApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepOrange"
        
        # Подгружаем все KV файлы декларативного дизайна
        Builder.load_file("screens/splash_screen/splash.kv")
        Builder.load_file("screens/search_screen/search.kv")
        Builder.load_file("screens/profile_screen/profile.kv")
        Builder.load_file("screens/settings_screen/settings.kv")
        
        # Настраиваем менеджер окон со слайд-анимациями перехода
        sm = ScreenManager(transition=SlideTransition())
        
        # Порядок добавления определяет стартовый экран (первый — splash)
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(SearchScreen(name="search"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(SettingsScreen(name="settings"))
        
        return sm

if __name__ == "__main__":
    DotaStatsApp().run()