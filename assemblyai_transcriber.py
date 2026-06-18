"""
Transcripcion de reels de Instagram usando AssemblyAI.
Descarga el audio con yt-dlp (cookies del agent-browser) y sube a AssemblyAI.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

from config import ASSEMBLYAI_API_KEY

_TRANSCRIBER_DIR = Path(r"C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber")
if str(_TRANSCRIBER_DIR) not in sys.path:
    sys.path.insert(0, str(_TRANSCRIBER_DIR))

from scraper.agent_browser_session import get_instagram_cookies

_API_BASE = "https://api.assemblyai.com/v2"


def _write_netscape_cookies(cookies: list[dict], path: str):
    lines = ["# Netscape HTTP Cookie File\n"]
    for c in cookies:
        domain = c.get("domain", ".instagram.com")
        if not domain.startswith("."):
            domain = "." + domain
        secure = "TRUE" if c.get("secure") else "FALSE"
        expires = str(int(c.get("expirationDate", 0)))
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\tTRUE\t/\t{secure}\t{expires}\t{name}\t{value}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _download_audio(url: str, tmpdir: str, cookies_file: str) -> str | None:
    try:
        import yt_dlp
    except ImportError:
        print("  [assemblyai] yt-dlp no instalado. Instalar con: pip install yt-dlp")
        return None

    audio_template = os.path.join(tmpdir, "reel.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_template,
        "cookiefile": cookies_file,
        "quiet": True,
        "no_warnings": True,
    }

    # Intentar con FFmpeg (mp3); si no está disponible, usar formato nativo
    try:
        import subprocess
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "96",
        }]
        expected_ext = "mp3"
    except Exception:
        expected_ext = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if expected_ext:
                path = os.path.join(tmpdir, f"reel.{expected_ext}")
                if os.path.exists(path):
                    return path
            # Buscar cualquier archivo descargado en tmpdir
            for f in os.listdir(tmpdir):
                if f.startswith("reel.") and f != "reel.txt":
                    return os.path.join(tmpdir, f)
    except Exception as e:
        print(f"  [assemblyai] Error en yt-dlp: {e}")

    return None


def _upload_to_assemblyai(filepath: str) -> str | None:
    import requests
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    try:
        size_kb = os.path.getsize(filepath) // 1024
        print(f"  [assemblyai] Subiendo {size_kb} KB a AssemblyAI...")
        with open(filepath, "rb") as f:
            resp = requests.post(f"{_API_BASE}/upload", headers=headers, data=f, timeout=180)
        resp.raise_for_status()
        return resp.json()["upload_url"]
    except Exception as e:
        print(f"  [assemblyai] Error subiendo archivo: {e}")
        return None


def _request_transcript(upload_url: str) -> str | None:
    import requests
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json",
    }
    try:
        resp = requests.post(
            f"{_API_BASE}/transcript",
            headers=headers,
            json={"audio_url": upload_url, "language_detection": True},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]
    except Exception as e:
        print(f"  [assemblyai] Error solicitando transcripcion: {e}")
        return None


def _poll_transcript(trans_id: str, max_wait: int = 300) -> str:
    import requests
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    url = f"{_API_BASE}/transcript/{trans_id}"
    elapsed = 0
    interval = 5

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status == "completed":
                text = data.get("text", "")
                print(f"  [assemblyai] Transcript OK -- {len(text.split())} palabras.")
                return text
            if status == "error":
                print(f"  [assemblyai] Error en AssemblyAI: {data.get('error')}")
                return ""
        except Exception as e:
            print(f"  [assemblyai] Error en polling: {e}")

    print("  [assemblyai] Timeout esperando transcripcion.")
    return ""


def transcribe_reel(url: str) -> str:
    """
    Descarga el audio del reel y lo transcribe con AssemblyAI.
    Retorna el texto transcripto o '' si falla.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Escribir cookies
        cookies_file = os.path.join(tmpdir, "ig_cookies.txt")
        try:
            raw_cookies = get_instagram_cookies()
            _write_netscape_cookies(raw_cookies, cookies_file)
        except Exception as e:
            print(f"  [assemblyai] Error cargando cookies: {e}")
            return ""

        # 2. Descargar audio
        print(f"  [assemblyai] Descargando audio de {url}...")
        audio_path = _download_audio(url, tmpdir, cookies_file)
        if not audio_path:
            return ""

        # 3. Subir a AssemblyAI
        upload_url = _upload_to_assemblyai(audio_path)
        if not upload_url:
            return ""

        # 4. Solicitar transcripcion
        trans_id = _request_transcript(upload_url)
        if not trans_id:
            return ""

        print(f"  [assemblyai] Transcribiendo (ID: {trans_id})...")

        # 5. Polling
        return _poll_transcript(trans_id)
