"""
Fase 1 — Extrae posts guardados de Instagram y los sube al Raw Saves DB (Stage=SIN ANALIZAR).
Ejecutado automaticamente por Windows Task Scheduler 2 veces al dia.

Uso:
  python sync.py
  python sync.py --dry-run    # Solo muestra que subiria, sin escribir en Notion
  python sync.py --limit 5    # Maximo N saves a subir
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import STATE_FILE
from ig_fetcher import fetch_saved_posts
from notion_db import add_raw_save


def _load_state() -> set:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return set(data.get("synced_ids", []))
        except (json.JSONDecodeError, KeyError):
            pass
    return set()


def _save_state(synced_ids: set):
    STATE_FILE.write_text(
        json.dumps({"synced_ids": list(synced_ids)}, indent=2),
        encoding="utf-8",
    )


def run(dry_run: bool = False, limit: int = 0):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{ts}] Iniciando sync -> Raw Saves DB...")

    synced_ids = _load_state()
    print(f"IDs ya sincronizados: {len(synced_ids)}")

    try:
        saves = fetch_saved_posts()
    except Exception as exc:
        print(f"[error] No se pudo conectar a Instagram: {exc}", file=sys.stderr)
        sys.exit(1)

    new_saves = [s for s in saves if s["media_id"] not in synced_ids]
    if limit:
        new_saves = new_saves[:limit]
    print(f"Posts guardados: {len(saves)} total | {len(new_saves)} nuevos")

    if not new_saves:
        print("Nada nuevo que sincronizar.")
        return

    uploaded = 0
    for save in new_saves:
        if dry_run:
            print(f"  [dry-run] @{save['author']} -- {save['content_type']} -- {save['url']}")
            continue

        try:
            url = add_raw_save(save)
            synced_ids.add(save["media_id"])
            print(f"  + @{save['author']} ({save['content_type']}) -> Verdict:SIN ANALIZAR -> {url}")
            uploaded += 1
        except Exception as exc:
            print(f"  [error] {save['url']}: {exc}", file=sys.stderr)

    if not dry_run:
        _save_state(synced_ids)
        print(f"Sync completado: {uploaded}/{len(new_saves)} subidos al Raw Saves DB.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Instagram saves -> Raw Saves DB")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en Notion")
    parser.add_argument("--limit", type=int, default=0, help="Maximo de saves a subir")
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)
