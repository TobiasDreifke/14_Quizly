import yt_dlp
import tempfile
import os


def download_youtube_audio(url: str) -> str:
    tmp_dir = tempfile.mkdtemp()
    tmp_filename = os.path.join(tmp_dir, "audio")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{tmp_filename}.mp3"



