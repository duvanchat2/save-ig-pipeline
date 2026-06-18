"""
Transcripcion de reels de Instagram usando AssemblyAI.
Descarga el audio con yt-dlp (sin autenticacion — funciona para reels publicos).
Si el reel es privado, la descarga fallara y se retorna "".
"""
import os
import tempfile
import time

from config import ASSEMBLYAI_API_KEY

_API_BASE = "https://api.assemblyai.com/v2"


def _download_audio(url: str, tmpdir: str) -> str | None:
    try:
        import yt_dlp
    except ImportError:
        print("  [assemblyai] yt-dlp no instalado: pip install yt-dlp")
        return None

    audio_template = os.path.join(tmpdir, "reel.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_template,
        "quiet": True,
        "no_warnings": True,
    }

    # Usar FFmpeg para extraer MP3 si está disponible
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
            ydl.extract_info(url, download=True)
            if expected_ext:
                path = os.path.join(tmpdir, f"reel.{expected_ext}")
                if os.path.exists(path):
                    return path
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
    Descarga el audio del reel publico y lo transcribe con AssemblyAI.
    Retorna el texto transcripto o '' si falla.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"  [assemblyai] Descargando audio de {url}...")
        audio_path = _download_audio(url, tmpdir)
        if not audio_path:
            print("  [assemblyai] No se pudo descargar el audio (reel privado o error de red).")
            return ""

        upload_url = _upload_to_assemblyai(audio_path)
        if not upload_url:
            return ""

        trans_id = _request_transcript(upload_url)
        if not trans_id:
            return ""

        print(f"  [assemblyai] Transcribiendo (ID: {trans_id})...")
        return _poll_transcript(trans_id)
