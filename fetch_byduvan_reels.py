"""
Bridge script: extrae reels de @byduvan_ai usando el scraper existente
(instagram-transcriber con cookies de agent-browser) y retorna JSON.

Uso:
  python fetch_byduvan_reels.py --count 20
"""
import sys
import json
import argparse
from pathlib import Path

# Agregar el instagram-transcriber al path para reutilizar su scraper
TRANSCRIBER_DIR = Path(r"C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber")
sys.path.insert(0, str(TRANSCRIBER_DIR))

from scraper.instagram import InstagramScraper

PROFILE_URL = "https://www.instagram.com/byduvan_ai/"


def fetch_reels(count: int = 30) -> list[dict]:
    print(f"[auth] Conectando con cookies de Instagram...", file=sys.stderr)
    scraper = InstagramScraper()

    print(f"[fetch] Obteniendo últimos {count} reels de @byduvan_ai...", file=sys.stderr)
    reels = scraper.get_profile_reels(PROFILE_URL, count)
    print(f"[fetch] {len(reels)} reels obtenidos.", file=sys.stderr)

    # Mapear al formato de Raw Saves
    saves = []
    for r in reels:
        saves.append({
            "media_id": r.get("id") or r.get("shortCode"),
            "url": r.get("instagramUrl", ""),
            "author": r.get("ownerUsername", "byduvan_ai"),
            "caption": (r.get("caption") or "")[:2000],
            "content_type": "Reel",
            "collection": "byduvan_ai — Propios",
            "thumbnail": r.get("displayUrl", ""),
            "taken_at": r.get("timestamp", ""),
            # Extras para referencia
            "likes": r.get("likesCount", 0),
            "views": r.get("videoViewCount", 0),
            "shortcode": r.get("shortCode", ""),
        })
    return saves


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20, help="Máximo de reels a obtener")
    args = parser.parse_args()

    saves = fetch_reels(args.count)
    print(json.dumps(saves, ensure_ascii=False, indent=2))
