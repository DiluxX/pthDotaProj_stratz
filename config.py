import os
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_dir
    STORE_PATH = os.path.join(app_storage_dir(), 'settings.json')
else:
    STORE_PATH = 'settings.json'

store = JsonStore(STORE_PATH)

# Инициализируем настройки дефолтными значениями, если файла еще нет.
# ВАЖНО: ключи Steam и Stratz - это два РАЗНЫХ ключа от разных сервисов,
# поэтому храним их отдельно, чтобы не путать (раньше был один общий "api_key",
# из-за чего один и тот же ключ пытались использовать для обоих API).
if not store.exists('app_settings'):
    store.put(
        'app_settings',
        api_key="",          # Steam Web API key (steamcommunity.com/dev/apikey)
        stratz_api_key="",   # Bearer-токен STRATZ (Settings -> API на stratz.com)
        app_theme="system",  # "system" | "purple" | "light"
    )
else:
    # Миграция для тех, у кого store уже существует, но нет нового поля
    data = store.get('app_settings')
    if 'stratz_api_key' not in data:
        data['stratz_api_key'] = ""
        store.put('app_settings', **data)