import os
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_dir
    STORE_PATH = os.path.join(app_storage_dir(), 'settings.json')
else:
    STORE_PATH = 'settings.json'

store = JsonStore(STORE_PATH)

if not store.exists('app_settings'):
    store.put(
        'app_settings',
        app_theme="system",  # "system" | "purple" | "light"
    )