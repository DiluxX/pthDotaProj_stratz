"""
Управление темами приложения.

Поддерживаются 3 варианта, которые выбирает пользователь в настройках:
  - "system" : подстраивается под системную тёмную/светлую тему устройства
  - "purple" : фиолетовый + тёмно-серый (всегда тёмная)
  - "light"  : светло-голубой + белый (всегда светлая)

Сохранённое значение - это ВЫБОР пользователя ("system"/"purple"/"light"),
а не итоговая палитра, поэтому при выборе "system" реальные цвета
пересчитываются на каждом запуске (вдруг пользователь сменил тему Windows/Android).
"""

from kivy.utils import platform
from config import store

_THEMES = {
    "system_dark": {
        "style": "Dark",
        "bg": (0.09, 0.09, 0.09, 1),
        "surface": (0.16, 0.16, 0.16, 1),
        "accent": (0.22, 0.28, 0.17, 1),
        "text": (1, 1, 1, 1),
        "secondary_text": (0.62, 0.62, 0.62, 1),
    },
    "system_light": {
        "style": "Light",
        "bg": (0.96, 0.96, 0.96, 1),
        "surface": (1, 1, 1, 1),
        "accent": (0.22, 0.28, 0.17, 1),
        "text": (0.1, 0.1, 0.1, 1),
        "secondary_text": (0.35, 0.35, 0.35, 1),
    },
    "purple": {
        "style": "Dark",
        "bg": (0.10, 0.09, 0.13, 1),
        "surface": (0.18, 0.15, 0.23, 1),
        "accent": (0.48, 0.27, 0.70, 1),
        "text": (1, 1, 1, 1),
        "secondary_text": (0.68, 0.63, 0.75, 1),
    },
    "light": {
        "style": "Light",
        "bg": (0.97, 0.98, 1, 1),
        "surface": (1, 1, 1, 1),
        "accent": (0.16, 0.55, 0.87, 1),
        "text": (0.08, 0.1, 0.14, 1),
        "secondary_text": (0.38, 0.44, 0.5, 1),
    },
}


def get_saved_theme_mode() -> str:
    if store.exists('app_settings'):
        return store.get('app_settings').get('app_theme', 'system')
    return 'system'


def save_theme_mode(mode: str):
    data = store.get('app_settings') if store.exists('app_settings') else {}
    data['app_theme'] = mode
    store.put('app_settings', **data)


def detect_system_is_dark() -> bool:
    """
    Best-effort определение тёмной/светлой темы ОС.
    Если платформа не поддерживается или что-то пошло не так - считаем тёмной
    (это исходная тема приложения, самый безопасный дефолт).
    """
    try:
        if platform == "win":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0  # 0 = тёмная, 1 = светлая
        elif platform == "android":
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            config = activity.getResources().getConfiguration()
            ui_mode = config.uiMode & 48  # Configuration.UI_MODE_NIGHT_MASK == 48
            UI_MODE_NIGHT_YES = 32
            return ui_mode == UI_MODE_NIGHT_YES
    except Exception as e:
        print(f"[DEBUG] Не удалось определить системную тему: {e}")

    return True  # безопасный дефолт - тёмная


def resolve_theme(mode: str) -> dict:
    """Превращает выбор пользователя ("system"/"purple"/"light") в конкретную палитру."""
    if mode == "purple":
        return _THEMES["purple"]
    if mode == "light":
        return _THEMES["light"]

    # mode == "system" (или что-то незнакомое - тоже считаем системным)
    return _THEMES["system_dark"] if detect_system_is_dark() else _THEMES["system_light"]