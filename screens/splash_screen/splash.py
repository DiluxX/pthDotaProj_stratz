from kivymd.uix.screen import MDScreen
from kivy.clock import Clock

class SplashScreen(MDScreen):
    def on_enter(self):
        # Имитируем загрузку приложения в 2.5 секунды, затем идем в поиск
        Clock.schedule_once(self.switch_to_main, 2.5)

    def switch_to_main(self, dt):
        self.manager.transition.direction = "left"
        self.manager.current = "search"