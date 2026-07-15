from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI()

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
STRATZ_API_TOKEN = os.environ.get("STRATZ_API_TOKEN")

# Проверочный эндпоинт, чтобы сразу видеть статус в браузере!
@app.get("/")
@app.get("/api")
async def root_test():
    return {
        "status": "ok",
        "message": "Dota 2 Proxy Backend is successfully running!",
        "steam_key_detected": STEAM_API_KEY is not None,
        "stratz_token_detected": STRATZ_API_TOKEN is not None
    }

# 1. Получение профиля (работает и с /api, и без него)
@app.get("/api/steam/player_summaries")
@app.get("/steam/player_summaries")
async def get_player_summaries(steamids: str):
    if not STEAM_API_KEY:
        raise HTTPException(status_code=500, detail="STEAM_API_KEY is not configured on Vercel")
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    params = {"key": STEAM_API_KEY, "steamids": steamids}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

# 2. История матчей
@app.get("/api/steam/match_history")
@app.get("/steam/match_history")
async def get_match_history(account_id: str):
    if not STEAM_API_KEY:
        raise HTTPException(status_code=500, detail="STEAM_API_KEY is not configured on Vercel")
    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v0001/"
    params = {"key": STEAM_API_KEY, "account_id": account_id}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

# 3. Преобразование Vanity URL
@app.get("/api/steam/resolve_vanity")
@app.get("/steam/resolve_vanity")
async def resolve_vanity(vanityurl: str):
    if not STEAM_API_KEY:
        raise HTTPException(status_code=500, detail="STEAM_API_KEY is not configured on Vercel")
    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
    params = {"key": STEAM_API_KEY, "vanityurl": vanityurl}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

# 4. GraphQL-запросы к Stratz
@app.post("/api/stratz/graphql")
@app.post("/stratz/graphql")
async def stratz_graphql(payload: dict):
    if not STRATZ_API_TOKEN:
        raise HTTPException(status_code=500, detail="STRATZ_API_TOKEN is not configured on Vercel")
    url = "https://api.stratz.com/graphql"
    headers = {
        "User-Agent": "STRATZ_API",
        "Authorization": f"Bearer {STRATZ_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/graphql-response+json, application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))