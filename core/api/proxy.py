from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Твой секретный ключ, который ты укажешь в настройках Vercel
        api_key = os.environ.get("STEAM_API_KEY")
        
        # Пример проксирования запроса к Steam
        # В реальной задаче ты будешь парсить путь и параметры из self.path
        target_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=" + api_key + "&steamids=..."
        
        try:
            with urllib.request.urlopen(target_url) as response:
                data = response.read().decode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(data.encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()