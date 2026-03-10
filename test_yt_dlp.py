from quizzes_app.API.utils import download_youtube_audio

url = "https://www.youtube.com/watch?v=Rf2yAxnTCxc"

print(" Download startet...")
path = download_youtube_audio(url)
print(f" Datei gespeichert unter: {path}")


import os
print(f" Datei existiert: {os.path.exists(path)}")
print(f" Dateigröße: {os.path.getsize(path)} bytes")

