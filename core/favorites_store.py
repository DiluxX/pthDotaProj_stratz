"""Хранение списка избранных игроков в отдельном JSON-хранилище."""

import os
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_dir
    _STORE_PATH = os.path.join(app_storage_dir(), 'favorites.json')
else:
    _STORE_PATH = 'favorites.json'

_store = JsonStore(_STORE_PATH)


def get_favorites() -> list:
    """Возвращает список избранных игроков: [{account_id, personaname, avatar}, ...]"""
    if not _store.exists('players'):
        return []
    return _store.get('players').get('list', [])


def is_favorite(account_id: str) -> bool:
    account_id = str(account_id)
    return any(p.get("account_id") == account_id for p in get_favorites())


def add_favorite(account_id: str, personaname: str, avatar: str = ""):
    account_id = str(account_id)
    favorites = get_favorites()
    if any(p.get("account_id") == account_id for p in favorites):
        return  # уже в избранном
    favorites.append({
        "account_id": account_id,
        "personaname": personaname or f"ID {account_id}",
        "avatar": avatar or "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
    })
    _store.put('players', list=favorites)


def remove_favorite(account_id: str):
    account_id = str(account_id)
    favorites = [p for p in get_favorites() if p.get("account_id") != account_id]
    _store.put('players', list=favorites)