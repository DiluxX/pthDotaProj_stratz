import httpx
import urllib.parse
from config import store

def get_steam_api_key():
    """Достает сохраненный пользователем ключ из локального JsonStore"""
    try:
        return store.get('app_settings')['api_key'].strip()
    except KeyError:
        return ""

def search_players_by_name(name: str) -> list:
    """
    Ищет игроков по никнейму через официальный открытый API OpenDota.
    Безопасно кодирует спецсимволы и кириллицу.
    """
    if not name.strip():
        return []
        
    # Шаг 1: Основной поиск по никнейму через OpenDota API
    encoded_name = urllib.parse.quote(name.strip())
    url = f"https://api.opendota.com/api/search?q={encoded_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        with httpx.Client(headers=headers, timeout=7.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                results = response.json()
                if results:
                    players_list = []
                    for p in results[:10]: # Ограничиваемся топ-10 совпадений
                        account_id = p.get("account_id")
                        if account_id:
                            players_list.append({
                                "account_id": str(account_id),
                                "personaname": p.get("personaname") or "Без никнейма",
                                "avatar": p.get("avatarfull") or p.get("avatar") or "https://steamloopback.host/images/default_avatar.jpg"
                            })
                    print(f"[DEBUG] Через OpenDota API успешно найдено игроков: {len(players_list)}")
                    return players_list
            print(f"[DEBUG] OpenDota вернула код {response.status_code} или пустой список.")
    except Exception as e:
        print(f"[DEBUG] Исключение при поиске через OpenDota: {e}")

    # Шаг 2: Резервный план. Если OpenDota лежит, проверяем текст как прямую ссылку/Vanity URL
    print("[DEBUG] Смена стратегии: Проверка текста как Vanity URL через Valve API...")
    try:
        vanity_id = resolve_steam_vanity_url(name.strip())
        if vanity_id:
            return [{
                "account_id": vanity_id,
                "personaname": name.strip(),
                "avatar": "https://steamloopback.host/images/default_avatar.jpg"
            }]
    except Exception as e:
        print(f"[DEBUG] Не удалось разрешить Vanity URL в резервном режиме: {e}")
        
    return []

def get_player_profile_from_valve(steam_id: str) -> dict:
    """Получает данные профиля и историю матчей напрямую через Steam Web API"""
    api_key = get_steam_api_key()
    if not api_key:
        raise Exception("В настройках приложения не указан Steam API Key!")

    if len(steam_id) < 17:
        steam_id_64 = str(int(steam_id) + 76561197960265728)
    else:
        steam_id_64 = steam_id
        steam_id = str(int(steam_id) - 76561197960265728)

    result = {}
    user_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id_64}"
    match_url = f"https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v0001/?key={api_key}&account_id={steam_id}"

    try:
        with httpx.Client(timeout=10.0) as client:
            user_res = client.get(user_url)
            user_res.raise_for_status()
            user_data = user_res.json()
            
            players = user_data.get("response", {}).get("players", [])
            if players:
                result["name"] = players[0].get("personaname", "Unknown")
                result["avatar"] = players[0].get("avatarfull", "")
            else:
                result["name"] = "Скрытый профиль"

            match_res = client.get(match_url)
            if match_res.status_code == 200:
                match_data = match_res.json()
                matches = match_data.get("result", {}).get("matches", [])
                result["matches_count"] = len(matches)
                
                if result["matches_count"] == 100:
                    result["matches_text"] = "Последние 100 матчей (лимит API)"
                else:
                    result["matches_text"] = f"Доступно матчей: {result['matches_count']}"
            else:
                result["matches_text"] = "История матчей скрыта в настройках Dota 2"

            return result

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise Exception("Невалидный API-ключ! Проверьте его в настройках.")
        raise Exception(f"Ошибка сервера Valve: {e.response.status_code}")
    except Exception as e:
        raise Exception(f"Ошибка соединения: {str(e)}")
    
def resolve_steam_vanity_url(vanity_name: str) -> str:
    """Преобразует буквенный никнейм ссылки в числовой ID через Steam Web API"""
    api_key = get_steam_api_key()
    if not api_key:
        return ""
        
    vanity_name = vanity_name.strip().rstrip('/')
    if "steamcommunity.com/id/" in vanity_name:
        vanity_name = vanity_name.split("/id/")[-1]
    elif "steamcommunity.com/profiles/" in vanity_name:
        return vanity_name.split("/profiles/")[-1]

    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={api_key}&vanityurl={vanity_name}"
    
    try:
        with httpx.Client(timeout=7.0) as client:
            response = client.get(url)
            print(f"[DEBUG LOG] Отправлен запрос: {url}")
            print(f"[DEBUG LOG] Статус ответа Valve: {response.status_code}")
            
            data = response.json().get("response", {})
            print(f"[DEBUG LOG] Данные от Valve: {data}")
            
            if data.get("success") == 1:
                steam_id_64 = int(data.get("steamid"))
                account_id = str(steam_id_64 - 76561197960265728)
                print(f"[DEBUG LOG] Успешно сконвертировано в ID Доты: {account_id}")
                return account_id
                
            print("[DEBUG LOG] Valve вернул success != 1 (такой Vanity URL не существует)")
            return ""
    except Exception as e:
        print(f"[DEBUG LOG] Ошибка внутри функции: {e}")
        return ""
    
    """Доделать чтобы выводилось несколько пользователей, если совпадений несколько. Сейчас выводится только первый найденный аккаунт."""
    """Сделать отображение аватарки игрока в списке результатов поиска, чтобы было наглядно видно, кто это."""
    """Сделать корректное отображение id и никнейма в списке результатов поиска, чтобы было понятно, кто это."""