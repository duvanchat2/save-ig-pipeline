"""
Extrae posts guardados de Instagram.

Modo AUTO: detecta qué credenciales están disponibles.
  1. META_ACCESS_TOKEN en .env  → usa Meta Graph API (recomendado)
  2. ig_cookies.json en el proyecto → usa cookies del navegador Chrome

Uso:
  python ig_fetcher.py --test      # Verifica la autenticación activa
  python ig_fetcher.py             # Retorna saves como JSON a stdout
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import META_ACCESS_TOKEN, IG_USER_ID, BASE_DIR

_COOKIES_FILE = BASE_DIR / "ig_cookies.json"

# ── Modo 1: Meta Graph API ─────────────────────────────────────────────────────
_GRAPH_BASE = "https://graph.facebook.com/v19.0"
_FIELDS = (
    "id,caption,media_type,media_url,permalink,"
    "timestamp,username,like_count,comments_count,thumbnail_url"
)


def _media_type_label_graph(media_type: str) -> str:
    return {"IMAGE": "Post", "VIDEO": "Reel", "CAROUSEL_ALBUM": "Carousel"}.get(media_type, "Post")


def _fetch_via_meta(max_posts: int = 50) -> list[dict]:
    results = []
    url = f"{_GRAPH_BASE}/{IG_USER_ID}/saved_media"
    params = {"fields": _FIELDS, "access_token": META_ACCESS_TOKEN, "limit": 25}

    while len(results) < max_posts:
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as e:
            err = (e.response.json() if e.response else {}).get("error", {})
            code = err.get("code")
            print(f"[ig] Error Graph API {code}: {err.get('message')}", file=sys.stderr)
            if code == 190:
                print("[ig] Token expirado. Renovar en Meta Developer Portal.", file=sys.stderr)
            if code == 200:
                print("[ig] Falta permiso user_saved_media en el token.", file=sys.stderr)
            break
        except Exception as e:
            print(f"[ig] Error de conexion: {e}", file=sys.stderr)
            break

        for item in data.get("data", []):
            results.append({
                "media_id":    item.get("id", ""),
                "url":         item.get("permalink", ""),
                "media_url":   item.get("media_url") or item.get("thumbnail_url", ""),
                "author":      item.get("username", ""),
                "caption":     (item.get("caption") or "")[:2000],
                "content_type": _media_type_label_graph(item.get("media_type", "IMAGE")),
                "collection":  "Saved",
                "taken_at":    item.get("timestamp", ""),
                "views":       0,
                "likes":       item.get("like_count") or 0,
                "comments":    item.get("comments_count") or 0,
            })
            if len(results) >= max_posts:
                break

        next_url = data.get("paging", {}).get("next")
        if not next_url or len(results) >= max_posts:
            break
        url = next_url
        params = {}

    return results


# ── Modo 2: Cookies del navegador Chrome ──────────────────────────────────────
_IG_APP_ID = "936619743392459"
_SAVED_URL  = "https://www.instagram.com/api/v1/feed/saved/posts/"


def _load_cookies() -> dict:
    raw = json.loads(_COOKIES_FILE.read_text(encoding="utf-8"))
    return {c["name"]: c["value"] for c in raw}


def _make_headers(cookies: dict) -> dict:
    return {
        "x-ig-app-id":      _IG_APP_ID,
        "x-csrftoken":      cookies.get("csrftoken", ""),
        "x-requested-with": "XMLHttpRequest",
        "accept":           "*/*",
        "accept-language":  "en-US,en;q=0.9",
        "referer":          "https://www.instagram.com/",
        "origin":           "https://www.instagram.com",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }


def _ig_get(url: str, headers: dict, cookies: dict, params: dict = None) -> dict:
    import urllib.request, urllib.parse
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={**headers, "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _media_type_label_ig(media_type: int, product_type: str) -> str:
    if media_type == 2:
        return "Reel" if product_type == "clips" else "Video"
    if media_type == 8:
        return "Carousel"
    return "Post"


def _item_to_save_ig(item: dict) -> dict:
    media = item.get("media", item)
    shortcode = media.get("code") or media.get("shortcode", "")
    taken_at  = media.get("taken_at", 0)
    caption_obj = media.get("caption") or {}
    caption = caption_obj.get("text", "") if isinstance(caption_obj, dict) else str(caption_obj or "")
    user = media.get("user", {}) or {}
    ts = datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat() if taken_at else ""

    return {
        "media_id":    str(media.get("pk") or media.get("id", "")),
        "url":         f"https://www.instagram.com/reel/{shortcode}/" if shortcode else "",
        "media_url":   "",
        "author":      user.get("username", ""),
        "caption":     caption[:2000],
        "content_type": _media_type_label_ig(media.get("media_type", 1), media.get("product_type", "")),
        "collection":  "Saved",
        "taken_at":    ts,
        "views":       media.get("view_count") or media.get("play_count") or 0,
        "likes":       media.get("like_count") or 0,
        "comments":    media.get("comment_count") or 0,
    }


def _fetch_via_browser(max_posts: int = 50) -> list[dict]:
    cookies = _load_cookies()
    headers = _make_headers(cookies)
    results = []
    next_max_id = None

    while len(results) < max_posts:
        params = {"num_results": "20"}
        if next_max_id:
            params["max_id"] = next_max_id
        try:
            data = _ig_get(_SAVED_URL, headers, cookies, params)
        except Exception as e:
            print(f"[ig] Error API Instagram: {e}", file=sys.stderr)
            break

        for item in data.get("items", []):
            save = _item_to_save_ig(item)
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


# ── Selector de modo ──────────────────────────────────────────────────────────
def _detect_mode() -> str:
    if META_ACCESS_TOKEN and IG_USER_ID:
        return "meta"
    if _COOKIES_FILE.exists():
        return "browser"
    return "none"


def fetch_saved_posts(max_posts: int = 50) -> list[dict]:
    mode = _detect_mode()
    if mode == "meta":
        print(f"[ig] Modo: Meta Graph API (usuario {IG_USER_ID})")
        return _fetch_via_meta(max_posts)
    elif mode == "browser":
        print(f"[ig] Modo: cookies del navegador ({_COOKIES_FILE.name})")
        return _fetch_via_browser(max_posts)
    else:
        print("[ig] ERROR: No hay credenciales configuradas.", file=sys.stderr)
        print("[ig] Opciones:", file=sys.stderr)
        print("[ig]   1. Agregar META_ACCESS_TOKEN e IG_USER_ID al .env", file=sys.stderr)
        print("[ig]   2. Ejecutar /setup-instagram en Claude Code para extraer cookies", file=sys.stderr)
        sys.exit(1)


# ── Test ──────────────────────────────────────────────────────────────────────
def cmd_test():
    mode = _detect_mode()
    print(f"[ig] Modo detectado: {mode.upper()}")

    if mode == "meta":
        try:
            resp = requests.get(
                f"{_GRAPH_BASE}/me",
                params={"fields": "id,name", "access_token": META_ACCESS_TOKEN},
                timeout=15,
            )
            resp.raise_for_status()
            me = resp.json()
            print(f"[ig] Token valido — ID: {me.get('id')} | Nombre: {me.get('name')}")
        except Exception as e:
            print(f"[ig] Error verificando token: {e}", file=sys.stderr)
            return

    elif mode == "browser":
        cookies = _load_cookies()
        print(f"[ig] Cookies cargadas: {len(cookies)} | sessionid: {'SI' if 'sessionid' in cookies else 'NO'}")

    saves = fetch_saved_posts(max_posts=3)
    print(f"[ig] Saves obtenidos (muestra): {len(saves)}")
    for s in saves:
        print(f"  • @{s['author']} — {s['content_type']} — {s['url']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--max", type=int, default=50)
    args = parser.parse_args()
    if args.test:
        cmd_test()
    else:
        saves = fetch_saved_posts(max_posts=args.max)
        print(json.dumps(saves, ensure_ascii=False, indent=2))
