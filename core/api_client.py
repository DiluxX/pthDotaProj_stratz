import httpx
import urllib.parse
from config import store

# ---------------------------------------------------------------------------
# ТВОЙ СЕКРЕТНЫЙ АДРЕС НА VERCEL
# ---------------------------------------------------------------------------
VERCEL_PROXY_URL = "https://pth-dota-proj-stratz-i3gwy94o3-diluxxs-projects.vercel.app"

# ---------------------------------------------------------------------------
# Ключи (Локально больше не хранятся, сервер Vercel подставит их сам)
# ---------------------------------------------------------------------------

def get_steam_api_key():
    """Больше не считывает ключ локально. Оставлено для совместимости."""
    return ""


def get_stratz_api_key():
    """Больше не считывает токен локально. Оставлено для совместимости."""
    return ""


# ---------------------------------------------------------------------------
# Разбор ввода пользователя: ID / SteamID64 / ссылка на профиль / vanity-имя
# ---------------------------------------------------------------------------

def parse_steam_id_input(text: str) -> str:
    """
    Распознаёт в тексте прямую ссылку на Steam-профиль, голый
    SteamID64/account_id или короткое vanity-имя и возвращает 32-битный
    account_id. Возвращает "" если распознать не удалось.
    """
    text = text.strip().rstrip('/')
    if not text:
        return ""

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

    # Короткое слово без пробелов - пробуем как vanity-имя (custom URL).
    if " " not in text and all(ch.isascii() and ch.isalnum() for ch in text):
        return resolve_steam_vanity_url(text)

    return ""


def _steam64_to_account_id(steam_id_64: str) -> str:
    return str(int(steam_id_64) - 76561197960265728)


def resolve_steam_vanity_url(vanity_name: str) -> str:
    """Преобразует буквенный никнейм ссылки в числовой ID через твой Vercel-прокси"""
    vanity_name = vanity_name.strip().rstrip('/')
    if "steamcommunity.com/id/" in vanity_name:
        vanity_name = vanity_name.split("/id/")[-1]
    elif "steamcommunity.com/profiles/" in vanity_name:
        return vanity_name.split("/profiles/")[-1]

    url = f"{VERCEL_PROXY_URL}/api/steam/resolve_vanity"

    try:
        with httpx.Client(timeout=7.0) as client:
            response = client.get(url, params={"vanityurl": vanity_name})
            data = response.json().get("response", {})
            if data.get("success") == 1:
                steam_id_64 = int(data.get("steamid"))
                return str(steam_id_64 - 76561197960265728)
            return ""
    except Exception as e:
        print(f"[DEBUG LOG] Ошибка при резолве Vanity URL через Vercel: {e}")
        return ""


# ---------------------------------------------------------------------------
# Профиль игрока
# ---------------------------------------------------------------------------

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
    ranks {
      rank
    }
  }
}
"""

_RANK_MEDALS = {
    1: "Рекрут", 2: "Страж", 3: "Крестоносец", 4: "Архонт",
    5: "Легенда", 6: "Властелин", 7: "Божество", 8: "Титан",
}


def _decode_rank(rank_value) -> str:
    if not rank_value:
        return "Не откалиброван"
    medal, stars = divmod(int(rank_value), 10)
    medal_name = _RANK_MEDALS.get(medal)
    if not medal_name:
        return f"Ранг #{rank_value}"
    return f"{medal_name} {stars}" if stars else medal_name


def get_player_profile_from_stratz(account_id: str) -> dict:
    """
    Тянет профиль из STRATZ GraphQL API через твой безопасный Vercel-прокси.
    """
    url = f"{VERCEL_PROXY_URL}/api/stratz/graphql"
    
    payload = {
        "query": _STRATZ_PLAYER_QUERY,
        "variables": {"steamAccountId": int(account_id)},
    }

    with httpx.Client(timeout=12.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()

        body = response.json()
        if body.get("errors"):
            raise Exception(f"STRATZ GraphQL ошибка через Vercel: {body['errors']}")

        player = (body.get("data") or {}).get("player")
        if not player:
            raise Exception("STRATZ не вернул данные по этому steamAccountId")

        steam_account = player.get("steamAccount") or {}
        match_count = player.get("matchCount") or 0
        win_count = player.get("winCount") or 0
        winrate = round((win_count / match_count) * 100, 1) if match_count else 0.0

        ranks = player.get("ranks") or []
        rank_value = ranks[0].get("rank") if ranks else None

        return {
            "name": steam_account.get("name") or "Неизвестный",
            "avatar": steam_account.get("avatar") or "",
            "matches_count": match_count,
            "matches_text": f"Матчей в базе STRATZ: {match_count}",
            "winrate": winrate,
            "rank": _decode_rank(rank_value),
            "source": "stratz",
        }


def get_player_profile_from_valve(steam_id: str) -> dict:
    """Получает данные профиля и историю матчей через прокси-эндпоинты Steam на Vercel"""
    if len(steam_id) < 17:
        steam_id_64 = str(int(steam_id) + 76561197960265728)
    else:
        steam_id_64 = steam_id
        steam_id = str(int(steam_id) - 76561197960265728)

    result = {"source": "valve"}
    user_url = f"{VERCEL_PROXY_URL}/api/steam/player_summaries"
    match_url = f"{VERCEL_PROXY_URL}/api/steam/match_history"

    try:
        with httpx.Client(timeout=10.0) as client:
            user_res = client.get(user_url, params={"steamids": steam_id_64})
            user_res.raise_for_status()
            user_data = user_res.json()

            players = user_data.get("response", {}).get("players", [])
            if players:
                result["name"] = players[0].get("personaname", "Unknown")
                result["avatar"] = players[0].get("avatarfull", "")
            else:
                result["name"] = "Скрытый профиль"

            match_res = client.get(match_url, params={"account_id": steam_id})
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

    except Exception as e:
        raise Exception(f"Ошибка соединения с Vercel-прокси: {str(e)}")


def get_player_profile(account_id: str) -> dict:
    """
    Единая точка входа для экрана профиля: сначала пробуем безопасный STRATZ через Vercel,
    при любой ошибке — прозрачно откатываемся на Steam Web API через Vercel.
    """
    try:
        return get_player_profile_from_stratz(account_id)
    except Exception as stratz_err:
        print(f"[DEBUG] STRATZ через Vercel недоступен ({stratz_err}), откат на Steam API через Vercel")
        return get_player_profile_from_valve(account_id)


# ---------------------------------------------------------------------------
# Последние матчи
# ---------------------------------------------------------------------------

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

_HERO_NAMES_CACHE = {}

_STRATZ_RECENT_MATCHES_QUERY = """
query RecentMatches($steamAccountId: Long!, $take: Int!) {
  player(steamAccountId: $steamAccountId) {
    matches(request: { take: $take }) {
      id
      didRadiantWin
      durationSeconds
      startDateTime
      players(steamAccountId: $steamAccountId) {
        heroId
        kills
        deaths
        assists
        isRadiant
      }
    }
  }
}
"""


def get_recent_matches(account_id: str, limit: int = 5) -> list:
    try:
        matches = _recent_matches_from_stratz(account_id, limit)
        if matches:
            return matches
    except Exception as e:
        print(f"[DEBUG] STRATZ matches недоступны через Vercel: {e}")

    try:
        return _recent_matches_from_opendota(account_id, limit)
    except Exception as e:
        print(f"[DEBUG] OpenDota matches недоступны: {e}")

    return []


def _recent_matches_from_stratz(account_id: str, limit: int) -> list:
    url = f"{VERCEL_PROXY_URL}/api/stratz/graphql"
    
    payload = {
        "query": _STRATZ_RECENT_MATCHES_QUERY,
        "variables": {"steamAccountId": int(account_id), "take": limit},
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise Exception(f"STRATZ GraphQL ошибка истории матчей: {body['errors']}")

        raw_matches = ((body.get("data") or {}).get("player") or {}).get("matches") or []
        hero_names = _get_hero_names()
        result = []
        for m in raw_matches[:limit]:
            players = m.get("players") or []
            if not players:
                continue
            p = players[0]
            won = bool(m.get("didRadiantWin")) == bool(p.get("isRadiant"))
            result.append({
                "hero_name": hero_names.get(p.get("heroId"), f"Герой #{p.get('heroId')}"),
                "result": "Победа" if won else "Поражение",
                "won": won,
                "kda": f"{p.get('kills', 0)}/{p.get('deaths', 0)}/{p.get('assists', 0)}",
                "duration": _format_duration(m.get("durationSeconds")),
                "date": _format_timestamp(m.get("startDateTime")),
            })
        return result


def _recent_matches_from_opendota(account_id: str, limit: int) -> list:
    url = f"https://api.opendota.com/api/players/{account_id}/matches?limit={limit}"

    with httpx.Client(headers=_HTTP_HEADERS, timeout=6.0) as client:
        response = client.get(url)
        response.raise_for_status()
        raw_matches = response.json()

    hero_names = _get_hero_names()
    result = []
    for m in raw_matches[:limit]:
        won = (m.get("player_slot", 0) < 128) == bool(m.get("radiant_win"))
        result.append({
            "hero_name": hero_names.get(m.get("hero_id"), f"Герой #{m.get('hero_id')}"),
            "result": "Победа" if won else "Поражение",
            "won": won,
            "kda": f"{m.get('kills', 0)}/{m.get('deaths', 0)}/{m.get('assists', 0)}",
            "duration": _format_duration(m.get("duration")),
            "date": _format_timestamp(m.get("start_time")),
        })
    return result


def _get_hero_names() -> dict:
    global _HERO_NAMES_CACHE
    if _HERO_NAMES_CACHE:
        return _HERO_NAMES_CACHE
    try:
        with httpx.Client(headers=_HTTP_HEADERS, timeout=5.0) as client:
            response = client.get("https://api.opendota.com/api/heroes")
            response.raise_for_status()
            _HERO_NAMES_CACHE = {h["id"]: h.get("localized_name", f"Герой #{h['id']}") for h in response.json()}
    except Exception as e:
        print(f"[DEBUG] Не удалось получить список героев: {e}")
    return _HERO_NAMES_CACHE


def _format_duration(seconds) -> str:
    if not seconds:
        return "—"
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _format_timestamp(ts) -> str:
    if not ts:
        return "—"
    try:
        import datetime
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%d.%m.%Y")
    except Exception:
        return "—"


# ---------------------------------------------------------------------------
# Мета героев (винрейт по всем публичным брекетам OpenDota)
# ---------------------------------------------------------------------------

def get_hero_meta_stats() -> list:
    url = "https://api.opendota.com/api/heroStats"

    with httpx.Client(headers=_HTTP_HEADERS, timeout=8.0) as client:
        response = client.get(url)
        response.raise_for_status()
        raw_heroes = response.json()

    result = []
    for h in raw_heroes:
        picks = sum(h.get(f"{i}_pick") or 0 for i in range(1, 9))
        wins = sum(h.get(f"{i}_win") or 0 for i in range(1, 9))
        winrate = round((wins / picks) * 100, 1) if picks else 0.0

        img = h.get("img") or ""
        image_url = f"https://cdn.cloudflare.steamstatic.com{img}" if img else ""

        result.append({
            "id": h.get("id"),
            "name": h.get("localized_name", "Неизвестный герой"),
            "winrate": winrate,
            "picks": picks,
            "image": image_url,
            "is_meta": winrate > 51.0,
        })

    result.sort(key=lambda x: x["winrate"], reverse=True)
    return result