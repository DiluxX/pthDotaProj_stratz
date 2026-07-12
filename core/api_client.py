import time
import httpx
import urllib.parse
from config import store

# ---------------------------------------------------------------------------
# Ключи
# ---------------------------------------------------------------------------

def get_steam_api_key():
    """Steam Web API key (для api.steampowered.com)."""
    try:
        return store.get('app_settings').get('api_key', "").strip()
    except KeyError:
        return ""


def get_stratz_api_key():
    """Bearer-токен STRATZ (для api.stratz.com/graphql)."""
    try:
        return store.get('app_settings').get('stratz_api_key', "").strip()
    except KeyError:
        return ""


# ---------------------------------------------------------------------------
# Поиск игрока по нику (OpenDota)
#
# У STRATZ нет публичного эндпоинта полнотекстового поиска по нику - только
# поиск по конкретному steamAccountId. Поэтому для поиска по имени по-прежнему
# используем OpenDota, а STRATZ подключаем для самого профиля (см. ниже),
# где как раз и нужны свежие данные, ранг и винрейт.
# ---------------------------------------------------------------------------

_SEARCH_CACHE = {}
_SEARCH_CACHE_TTL = 60  # секунд - чтобы повторный ввод того же ника не бил API заново

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def search_players_by_name(name: str) -> list:
    """
    Ищет игроков по никнейму через OpenDota API.
    Возвращает СПИСОК всех найденных совпадений (а не только первое).
    Безопасно кодирует спецсимволы и кириллицу.
    """
    query = name.strip()
    if not query:
        return []

    cache_key = query.lower()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _SEARCH_CACHE_TTL:
        return cached[1]

    players_list = _search_via_opendota(query)

    # Данные в базе OpenDota обновляются только при парсинге новых матчей,
    # поэтому ник/аватар там могут быть старыми. Одним batch-запросом
    # подтягиваем АКТУАЛЬНЫЕ данные из Steam - это сразу покажет в списке,
    # если аккаунт с тех пор сменил ник (а значит, скорее всего, это не тот,
    # кого искали), вместо того чтобы выяснять это только после клика.
    if players_list:
        players_list = _refresh_with_current_steam_data(players_list, query)

    _SEARCH_CACHE[cache_key] = (time.time(), players_list)
    return players_list


def _refresh_with_current_steam_data(players: list, query: str) -> list:
    api_key = get_steam_api_key()
    if not api_key:
        return players

    ids64 = []
    for p in players:
        acc_id = p["account_id"]
        ids64.append(str(int(acc_id) + 76561197960265728))

    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        f"?key={api_key}&steamids={','.join(ids64)}"
    )

    try:
        with httpx.Client(timeout=6.0) as client:
            response = client.get(url)
            response.raise_for_status()
            current_by_id64 = {
                pl.get("steamid"): pl
                for pl in response.json().get("response", {}).get("players", [])
            }
    except Exception as e:
        print(f"[DEBUG] Не удалось актуализировать данные через Steam API: {e}")
        return players

    query_lower = query.strip().lower()
    for p, id64 in zip(players, ids64):
        current = current_by_id64.get(id64)
        if not current:
            continue  # приватный/удалённый профиль - оставляем данные OpenDota как есть

        current_name = current.get("personaname")
        if current_name:
            if current_name.strip().lower() != query_lower:
                p["personaname"] = f"{current_name}  ⚠ ник изменился, был «{p['personaname']}»"
            else:
                p["personaname"] = current_name
        if current.get("avatarfull"):
            p["avatar"] = current["avatarfull"]
        p["_exact_current_match"] = (current_name or "").strip().lower() == query_lower

    # Точные текущие совпадения - в начало списка
    players.sort(key=lambda x: not x.get("_exact_current_match", False))
    return players


def _search_via_opendota(query: str) -> list:
    encoded_name = urllib.parse.quote(query)
    url = f"https://api.opendota.com/api/search?q={encoded_name}"

    try:
        with httpx.Client(headers=_HTTP_HEADERS, timeout=5.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                results = response.json()
                players_list = []
                for p in results[:15]:  # ограничиваемся топ-15 совпадений
                    account_id = p.get("account_id")
                    if not account_id:
                        continue
                    personaname = p.get("personaname") or "Без никнейма"
                    players_list.append({
                        "account_id": str(account_id),
                        "personaname": personaname,
                        "avatar": p.get("avatarfull") or p.get("avatar") or "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
                        "last_match_time": p.get("last_match_time"),
                        # для сортировки: точное совпадение ника - в начало списка,
                        # иначе OpenDota может первым отдать однофамильца/тёзку
                        "_exact_match": personaname.strip().lower() == query.strip().lower(),
                    })

                players_list.sort(key=lambda x: (not x["_exact_match"], x["personaname"].lower()))
                for p in players_list:
                    p.pop("_exact_match", None)

                print(f"[DEBUG] OpenDota: найдено {len(players_list)} игроков по запросу '{query}'")
                return players_list
            print(f"[DEBUG] OpenDota вернула код {response.status_code}")
    except httpx.TimeoutException:
        print("[DEBUG] OpenDota не ответила за 5 секунд (timeout)")
    except Exception as e:
        print(f"[DEBUG] Исключение при поиске через OpenDota: {e}")

    return []


def parse_steam_id_input(text: str) -> str:
    """
    Пытается распознать в тексте прямую ссылку на Steam-профиль или голый
    SteamID64/account_id и вернуть 32-битный account_id.
    Возвращает "" если это обычный ник, а не ID/ссылка.
    """
    text = text.strip().rstrip('/')

    if "steamcommunity.com/profiles/" in text:
        raw_id = text.split("/profiles/")[-1].split("/")[0].strip()
        if raw_id.isdigit():
            return _steam64_to_account_id(raw_id)
        return ""

    if "steamcommunity.com/id/" in text:
        vanity = text.split("/id/")[-1].split("/")[0].strip()
        return resolve_steam_vanity_url(vanity)

    if text.isdigit():
        return _steam64_to_account_id(text) if len(text) >= 17 else text

    # Пользователь явно выбрал режим "по ID/ссылке" - значит короткое слово без
    # пробелов, скорее всего, тоже vanity-имя (custom URL), а не обычный ник.
    # Резолвим его напрямую через Steam Web API.
    if text and " " not in text and all(ch.isascii() and ch.isalnum() for ch in text):
        return resolve_steam_vanity_url(text)

    return ""


def _steam64_to_account_id(steam_id_64: str) -> str:
    return str(int(steam_id_64) - 76561197960265728)





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
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            data = response.json().get("response", {})
            if data.get("success") == 1:
                steam_id_64 = int(data.get("steamid"))
                return str(steam_id_64 - 76561197960265728)
            return ""
    except Exception as e:
        print(f"[DEBUG LOG] Ошибка при резолве Vanity URL: {e}")
        return ""


# ---------------------------------------------------------------------------
# Профиль игрока
#
# Пробуем сначала STRATZ (даёт актуальный ник/аватар/ранг/винрейт одним
# запросом), а если он недоступен (нет ключа, лимит, сеть) - откатываемся
# на Steam Web API, как было раньше.
# ---------------------------------------------------------------------------

STRATZ_GRAPHQL_URL = "https://api.stratz.com/graphql"

_STRATZ_PLAYER_QUERY = """
query PlayerProfile($steamAccountId: Long!) {
  player(steamAccountId: $steamAccountId) {
    steamAccount {
      id
      name
      avatar
    }
    matchCount
    winCount
  }
}
"""


def _stratz_headers():
    token = get_stratz_api_key()
    return {
        # Cloudflare у STRATZ блокирует запросы со стандартным User-Agent
        # httpx/requests - обязательно нужен осмысленный UA с контактом/названием приложения.
        "User-Agent": "pthDotaProj_stratz - Dota2Stats/1.0",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_player_profile_from_stratz(account_id: str) -> dict:
    """
    Тянет профиль напрямую из STRATZ GraphQL API.
    Бросает исключение, если ключ не задан, или STRATZ ответил ошибкой -
    вызывающий код должен откатиться на get_player_profile_from_valve.
    """
    token = get_stratz_api_key()
    if not token:
        raise Exception("STRATZ API ключ не задан в настройках")

    payload = {
        "query": _STRATZ_PLAYER_QUERY,
        "variables": {"steamAccountId": int(account_id)},
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(STRATZ_GRAPHQL_URL, headers=_stratz_headers(), json=payload)

        if response.status_code == 403:
            raise Exception(
                "STRATZ заблокировал запрос (403/Cloudflare). Проверь, что ключ "
                "действителен и не истёк."
            )
        response.raise_for_status()

        body = response.json()
        if body.get("errors"):
            raise Exception(f"STRATZ GraphQL ошибка: {body['errors']}")

        player = (body.get("data") or {}).get("player")
        if not player:
            raise Exception("STRATZ не вернул данные по этому steamAccountId")

        steam_account = player.get("steamAccount") or {}
        match_count = player.get("matchCount") or 0
        win_count = player.get("winCount") or 0
        winrate = round((win_count / match_count) * 100, 1) if match_count else 0.0

        return {
            "name": steam_account.get("name") or "Неизвестный",
            "avatar": steam_account.get("avatar") or "",
            "matches_count": match_count,
            "matches_text": f"Матчей в базе STRATZ: {match_count}",
            "winrate": winrate,
            "source": "stratz",
        }


def get_player_profile_from_valve(steam_id: str) -> dict:
    """Получает данные профиля и историю матчей напрямую через Steam Web API (запасной вариант)"""
    api_key = get_steam_api_key()
    if not api_key:
        raise Exception("В настройках приложения не указан Steam API Key!")

    if len(steam_id) < 17:
        steam_id_64 = str(int(steam_id) + 76561197960265728)
    else:
        steam_id_64 = steam_id
        steam_id = str(int(steam_id) - 76561197960265728)

    result = {"source": "valve"}
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
            raise Exception("Невалидный Steam API-ключ! Проверьте его в настройках.")
        raise Exception(f"Ошибка сервера Valve: {e.response.status_code}")
    except Exception as e:
        raise Exception(f"Ошибка соединения: {str(e)}")


def get_player_profile(account_id: str) -> dict:
    """
    Единая точка входа для экрана профиля: сначала пробуем STRATZ
    (свежие данные + винрейт одним запросом), при любой ошибке -
    прозрачно откатываемся на Steam Web API.
    """
    try:
        return get_player_profile_from_stratz(account_id)
    except Exception as stratz_err:
        print(f"[DEBUG] STRATZ недоступен ({stratz_err}), откат на Steam Web API")
        return get_player_profile_from_valve(account_id)