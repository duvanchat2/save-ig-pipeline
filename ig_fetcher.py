"""
Extrae posts guardados de Instagram usando las cookies del agent-browser
(mismo sistema que usa instagram-transcriber — sin contraseña).

Uso:
  python ig_fetcher.py --test      # Verifica cookies y muestra cuantos saves hay
  python ig_fetcher.py             # Retorna saves como JSON a stdout
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Importar agent_browser_session desde instagram-transcriber ────────────────
_TRANSCRIBER_DIR = Path(r"C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber")
if str(_TRANSCRIBER_DIR) not in sys.path:
    sys.path.insert(0, str(_TRANSCRIBER_DIR))

from scraper.agent_browser_session import get_instagram_cookies

# ── Endpoints de Instagram ─────────────────────────────────────────────────────
_IG_APP_ID   = "936619743392459"
_SAVED_URL   = "https://www.instagram.com/api/v1/feed/saved/posts/"
_COLLECT_URL = "https://www.instagram.com/api/v1/collections/list/"
_COLLECT_MEDIA_URL = "https://www.instagram.com/api/v1/feed/collection/{collection_id}/posts/"


def _make_headers(cookies: dict) -> dict:
    return {
        "x-ig-app-id": _IG_APP_ID,
        "x-csrftoken": cookies.get("csrftoken", ""),
        "x-requested-with": "XMLHttpRequest",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.instagram.com/",
        "origin": "https://www.instagram.com",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }


def _get(url: str, headers: dict, cookies: dict, params: dict = None) -> dict:
    import urllib.request, urllib.parse
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={**headers,
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _media_type_label(media_type: int, product_type: str) -> str:
    if media_type == 2:
        return "Reel" if product_type == "clips" else "Video"
    if media_type == 8:
        return "Carousel"
    return "Post"


def _item_to_save(item: dict, collection: str = "Saved") -> dict:
    media = item.get("media", item)  # algunos endpoints envuelven en "media"
    shortcode = media.get("code") or media.get("shortcode", "")
    taken_at = media.get("taken_at", 0)

    caption_obj = media.get("caption") or {}
    caption = caption_obj.get("text", "") if isinstance(caption_obj, dict) else str(caption_obj or "")

    user = media.get("user", {}) or {}
    media_type = media.get("media_type", 1)
    product_type = media.get("product_type", "") or ""

    ts = (datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat()
          if taken_at else "")

    return {
        "media_id": str(media.get("pk") or media.get("id", "")),
        "url": f"https://www.instagram.com/reel/{shortcode}/" if shortcode else "",
        "author": user.get("username", ""),
        "caption": caption[:2000],
        "content_type": _media_type_label(media_type, product_type),
        "collection": collection,
        "taken_at": ts,
        "views": (media.get("view_count") or media.get("play_count") or
                  media.get("video_view_count") or 0),
        "likes": media.get("like_count") or 0,
        "comments": media.get("comment_count") or 0,
    }


def fetch_saved_posts(max_posts: int = 50) -> list[dict]:
    """
    Descarga los posts guardados (coleccion principal) usando las cookies del agent-browser.
    """
    raw_cookies = get_instagram_cookies()
    cookies = {c["name"]: c["value"] for c in raw_cookies}
    headers = _make_headers(cookies)

    results = []
    next_max_id = None

    while len(results) < max_posts:
        params = {"num_results": "20"}
        if next_max_id:
            params["max_id"] = next_max_id

        try:
            data = _get(_SAVED_URL, headers, cookies, params)
        except Exception as e:
            print(f"[ig] Error al llamar API: {e}", file=sys.stderr)
            break

        items = data.get("items", [])
        for item in items:
            save = _item_to_save(item, "Saved")
            if save["media_id"]:
                results.append(save)
            if len(results) >= max_posts:
                break

        if not data.get("more_available"):
            break
        next_max_id = data.get("next_max_id")
        if not next_max_id:
            break

    return results


def cmd_test():
    print("[ig] Cargando cookies del agent-browser...")
    raw_cookies = get_instagram_cookies()
    cookies = {c["name"]: c["value"] for c in raw_cookies}
    print(f"[ig] {len(raw_cookies)} cookies cargadas — sessionid: {'SI' if 'sessionid' in cookies else 'NO'}")

    print("[ig] Probando endpoint de saves...")
    headers = _make_headers(cookies)
    data = _get(_SAVED_URL, headers, cookies, {"num_results": "3"})
    items = data.get("items", [])
    print(f"[ig] Saves encontrados (muestra 3): {len(items)}")
    for item in items:
        save = _item_to_save(item)
        print(f"  • @{save['author']} — {save['content_type']} — {save['url']}")
    print(f"[ig] more_available: {data.get('more_available')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Verificar cookies y mostrar muestra")
    parser.add_argument("--max", type=int, default=50, help="Maximo de saves a descargar")
    args = parser.parse_args()

    if args.test:
        cmd_test()
    else:
        saves = fetch_saved_posts(max_posts=args.max)
        print(json.dumps(saves, ensure_ascii=False, indent=2))
