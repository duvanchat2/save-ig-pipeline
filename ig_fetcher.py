"""
Extrae posts guardados de Instagram usando Meta Graph API.
Requiere un User Access Token con permiso user_saved_media
y el Instagram User ID de tu cuenta.

Uso:
  python ig_fetcher.py --test      # Verifica token y muestra muestra de saves
  python ig_fetcher.py             # Retorna saves como JSON a stdout
"""
import argparse
import json
import sys

import requests

from config import META_ACCESS_TOKEN, IG_USER_ID

_GRAPH_BASE = "https://graph.facebook.com/v19.0"
_FIELDS = (
    "id,caption,media_type,media_url,permalink,"
    "timestamp,username,like_count,comments_count,thumbnail_url"
)


def _media_type_label(media_type: str) -> str:
    return {
        "IMAGE": "Post",
        "VIDEO": "Reel",
        "CAROUSEL_ALBUM": "Carousel",
    }.get(media_type, "Post")


def _item_to_save(item: dict) -> dict:
    return {
        "media_id":    item.get("id", ""),
        "url":         item.get("permalink", ""),
        "media_url":   item.get("media_url") or item.get("thumbnail_url", ""),
        "author":      item.get("username", ""),
        "caption":     (item.get("caption") or "")[:2000],
        "content_type": _media_type_label(item.get("media_type", "IMAGE")),
        "collection":  "Saved",
        "taken_at":    item.get("timestamp", ""),
        "views":       0,  # Graph API no expone views para saves de terceros
        "likes":       item.get("like_count") or 0,
        "comments":    item.get("comments_count") or 0,
    }


def fetch_saved_posts(max_posts: int = 50) -> list[dict]:
    """
    Descarga los posts guardados via Meta Graph API.
    Requiere permiso user_saved_media en el token.
    """
    results = []
    url = f"{_GRAPH_BASE}/{IG_USER_ID}/saved_media"
    params = {
        "fields": _FIELDS,
        "access_token": META_ACCESS_TOKEN,
        "limit": 25,
    }

    while len(results) < max_posts:
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as e:
            body = e.response.json() if e.response else {}
            err = body.get("error", {})
            print(f"[ig] Error Graph API {err.get('code')}: {err.get('message')}", file=sys.stderr)
            if err.get("code") == 190:
                print("[ig] Token expirado o invalido. Renovar en Meta Developer Portal.", file=sys.stderr)
            if err.get("code") == 200:
                print("[ig] Permiso user_saved_media no habilitado en el token.", file=sys.stderr)
            break
        except Exception as e:
            print(f"[ig] Error de conexion: {e}", file=sys.stderr)
            break

        for item in data.get("data", []):
            save = _item_to_save(item)
            if save["media_id"]:
                results.append(save)
            if len(results) >= max_posts:
                break

        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url or len(results) >= max_posts:
            break
        url = next_url
        params = {}  # La URL "next" ya incluye todos los parámetros

    return results


def cmd_test():
    print("[ig] Verificando token con Meta Graph API...")
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

    print("[ig] Probando endpoint /saved_media (muestra 3)...")
    saves = fetch_saved_posts(max_posts=3)
    print(f"[ig] Saves obtenidos: {len(saves)}")
    for s in saves:
        print(f"  • @{s['author']} — {s['content_type']} — {s['url']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Verificar token y mostrar muestra")
    parser.add_argument("--max", type=int, default=50, help="Maximo de saves a descargar")
    args = parser.parse_args()

    if args.test:
        cmd_test()
    else:
        saves = fetch_saved_posts(max_posts=args.max)
        print(json.dumps(saves, ensure_ascii=False, indent=2))
