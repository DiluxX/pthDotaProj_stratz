[app]
title = Dota 2 Mobile Analyst
package.name = dotamobileanalyst
package.domain = org.mistersven

source.dir = .
source.include_exts = py, png, jpg, kv, json

# КРИТИЧЕСКИ ВАЖНО: Весь стек сетевых зависимостей для корректной компиляции под Android
requirements = python3, kivy==2.3.0, kivymd==1.2.0, httpx, certifi, idna, sniffio, anyio

orientation = portrait
fullscreen = 1

# Разрешение на использование интернета
android.permissions = INTERNET
android.api = 33
android.minapi = 21