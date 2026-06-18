"""
Fase 3 — Transforma saves aprobados en ideas de contenido para Content Ideas DB.
Lee Raw Saves donde Verdict=REPLICAR o ADAPTAR, busca transcript en Transcriber DB
(o lo genera con WhisperX), luego genera ideas con Claude y las sube a Content Ideas DB.

REPLICAR -> guion que replica la estructura del original adaptado al canal
ADAPTAR  -> contenido original que solo toma la formula/estructura

Uso:
  python transform.py                    # Interactivo
  python transform.py --auto             # Sin confirmacion
  python transform.py --limit 5          # Maximo N saves
  python transform.py --skip-transcribe  # No transcribe, usa solo caption
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from config import ANTHROPIC_API_KEY, CONTENT_NICHE, CONTENT_PILLARS
from notion_db import (
    get_unprocessed_saves,
    mark_save_processed,
    add_content_idea,
    update_save_transcript,
    get_transcript_by_shortcode,
)

# ── Rutas ──────────────────────────────────────────────────────────────────────
TRANSCRIBER_DIR = Path(r"C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber")
TRANSCRIBER_RESULTS = TRANSCRIBER_DIR / "output" / "results.json"
PYTHON = sys.executable

# ── Transcript helpers ─────────────────────────────────────────────────────────
def _shortcode_from_url(url: str) -> str:
    m = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else ""


def _read_transcript_file(shortcode: str) -> str:
    if not TRANSCRIBER_RESULTS.exists():
        return ""
    try:
        for entry in reversed(json.loads(TRANSCRIBER_RESULTS.read_text(encoding="utf-8"))):
            if entry.get("shortCode") == shortcode and entry.get("status") == "success":
                return entry.get("transcript", "")
    except Exception:
        pass
    return ""


def _get_transcript(save: dict) -> str:
    """Busca transcript en este orden: Raw Save -> Transcriber DB -> results.json -> WhisperX."""
    # 1. Ya guardado en el Raw Save
    if save.get("transcript"):
        print(f"  [transcript] Disponible en Raw Save ({len(save['transcript'].split())} palabras).")
        return save["transcript"]

    shortcode = _shortcode_from_url(save.get("url", ""))
    if not shortcode:
        return ""

    # 2. Transcriber DB de Notion
    t = get_transcript_by_shortcode(shortcode)
    if t:
        print(f"  [transcript] Encontrado en Transcriber DB ({len(t.split())} palabras).")
        return t

    # 3. results.json local
    t = _read_transcript_file(shortcode)
    if t:
        print(f"  [transcript] Encontrado en results.json ({len(t.split())} palabras).")
        return t

    # 4. Correr WhisperX
    print(f"  [transcript] Transcribiendo {shortcode} con WhisperX...")
    try:
        r = subprocess.run(
            [PYTHON, "main.py", "--reel", save.get("url", "")],
            cwd=str(TRANSCRIBER_DIR), capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            print(f"  [transcript] Error WhisperX: {r.stderr[-200:]}", file=sys.stderr)
            return ""
        t = _read_transcript_file(shortcode)
        if t:
            print(f"  [transcript] OK -- {len(t.split())} palabras.")
        return t
    except Exception as e:
        print(f"  [transcript] Error: {e}", file=sys.stderr)
        return ""


# ── System Prompts ─────────────────────────────────────────────────────────────
_PILLARS_STR = ", ".join(CONTENT_PILLARS)

_SYSTEM_REPLICAR = f"""Eres un estratega de contenido para @byduvan_ai.
Nicho: {CONTENT_NICHE}.
Pilares: {_PILLARS_STR}.

Este video es REPLICAR: organico, buenas metricas, formula clara.
Conserva la misma estructura, hook y ritmo del original, pero con tema
y ejemplos ajustados a nuestra audiencia de solopreneurs con IA.

RESPONDE UNICAMENTE con JSON valido (sin markdown):
{{
  "name": "Titulo para el canal (max 80 chars)",
  "pillar": "uno de: {_PILLARS_STR}",
  "format": "Carousel | Reel | Short Video | Long-form",
  "platforms": ["Instagram", "TikTok", "YouTube"],
  "priority": "High | Medium | Low",
  "hooks": "Hook 1 (curiosidad): ...\\nHook 2 (dolor): ...\\nHook 3 (resultado): ...",
  "outline": "HOOK: ...\\n\\nBODY:\\n1. ...\\n2. ...\\n3. ...\\n\\nCTA: ...",
  "guion": "Guion completo listo para grabar, mismo ritmo que el original adaptado a @byduvan_ai"
}}"""

_SYSTEM_ADAPTAR = f"""Eres un estratega de contenido para @byduvan_ai.
Nicho: {CONTENT_NICHE}.
Pilares: {_PILLARS_STR}.

Este video es ADAPTAR: la formula/estructura es valiosa pero el tema no es ideal
para replicacion directa. Crea contenido ORIGINAL para @byduvan_ai usando la misma
arquitectura narrativa con un tema nuevo relevante para nuestro nicho.

RESPONDE UNICAMENTE con JSON valido (sin markdown):
{{
  "name": "Titulo para el canal (max 80 chars)",
  "pillar": "uno de: {_PILLARS_STR}",
  "format": "Carousel | Reel | Short Video | Long-form",
  "platforms": ["Instagram", "TikTok", "YouTube"],
  "priority": "High | Medium | Low",
  "hooks": "Hook 1 (curiosidad): ...\\nHook 2 (dolor): ...\\nHook 3 (resultado): ...",
  "outline": "HOOK: ...\\n\\nBODY:\\n1. ...\\n2. ...\\n3. ...\\n\\nCTA: ...",
  "guion": "Guion original para @byduvan_ai usando la formula extraida, tema propio del nicho"
}}"""


def _build_msg(save: dict, transcript: str) -> str:
    v = save.get("views", 0) or 0
    l = save.get("likes", 0) or 0
    c = save.get("comments", 0) or 0
    cr = f"{c/v*100:.2f}%" if v > 0 else "N/D"
    lr = f"{l/v*100:.2f}%" if v > 0 else "N/D"
    tx = f"TRANSCRIPCION COMPLETA:\n{transcript}" if transcript else "TRANSCRIPCION: No disponible."
    f4 = save.get("f4_formula", "")
    formula_section = f"\nFORMULA DETECTADA:\n{f4}" if f4 else ""
    return (
        f"Veredicto: {save.get('verdict','')}\n"
        f"Creador: @{save.get('author','?')}\nTipo: {save.get('content_type','Reel')}\n"
        f"URL: {save.get('url','')}\n"
        f"Metricas: Views={v or 'N/D'} | Likes={l or 'N/D'} ({lr}) | Comments={c or 'N/D'} ({cr})\n"
        f"{formula_section}\n\n"
        f"CAPTION ORIGINAL:\n{save.get('caption','(sin caption)')}\n\n{tx}"
    )


def _generate(save: dict, transcript: str) -> dict:
    verdict = save.get("verdict", "ADAPTAR")
    system = _SYSTEM_REPLICAR if verdict == "REPLICAR" else _SYSTEM_ADAPTAR
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": _build_msg(save, transcript)}],
    )
    raw = re.sub(r"^```(?:json)?\s*", "", r.content[0].text.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _print_idea(idea: dict, save: dict):
    verdict = save.get("verdict", "")
    emoji = "REPLICAR" if verdict == "REPLICAR" else "ADAPTAR"
    sep = "=" * 60
    print(f"\n{sep}\n[{emoji}] @{save.get('author','?')}")
    print(f"IDEA: {idea.get('name')}")
    print(f"Pilar: {idea.get('pillar')} | Formato: {idea.get('format')} | Prioridad: {idea.get('priority')}")
    print(f"Plataformas: {', '.join(idea.get('platforms', []))}")
    print(f"\nHOOKS:\n{idea.get('hooks','')}")
    print(f"\nOUTLINE:\n{idea.get('outline','')}")
    if idea.get("guion"):
        preview = idea["guion"][:300]
        dots = "..." if len(idea["guion"]) > 300 else ""
        print(f"\nGUIÓN (preview):\n{preview}{dots}")
    print(sep)


# ── Orquestador ────────────────────────────────────────────────────────────────
def run(auto: bool = False, limit: int = 0, skip_transcribe: bool = False):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{ts}] Leyendo Raw Saves DB -- Verdict: REPLICAR / ADAPTAR...")

    saves = get_unprocessed_saves()
    if limit:
        saves = saves[:limit]
    if not saves:
        print("No hay saves listos para transformar.")
        return

    print(f"A transformar: {len(saves)}")
    processed = skipped = 0

    for i, save in enumerate(saves, 1):
        verdict = save.get("verdict", "?")
        print(f"\n[{i}/{len(saves)}] {verdict} -- @{save.get('author','?')} -- {save.get('url','')}")

        # Paso 1: obtener transcript
        transcript = ""
        if not skip_transcribe:
            transcript = _get_transcript(save)
            if transcript and not save.get("transcript"):
                # Guarda en Raw Save para no volver a transcribir
                update_save_transcript(save["page_id"], transcript)
        elif save.get("transcript"):
            transcript = save["transcript"]

        # Paso 2: generar idea con Claude
        action = "guion" if verdict == "REPLICAR" else "idea adaptada"
        print(f"  [claude] Generando {action} {'con transcript' if transcript else 'solo con caption'}...")
        try:
            idea = _generate(save, transcript)
        except json.JSONDecodeError as e:
            print(f"  [error] JSON invalido de Claude: {e}", file=sys.stderr)
            skipped += 1
            continue
        except Exception as e:
            print(f"  [error] Claude API: {e}", file=sys.stderr)
            skipped += 1
            continue

        idea["source_page_id"] = save["page_id"]
        # Mover campo guion a outline si viene separado
        if idea.get("guion") and not idea.get("outline"):
            idea["outline"] = idea["guion"]

        _print_idea(idea, save)

        if not auto:
            ans = input("Guardar en Content Ideas DB? [s/n/q]: ").strip().lower()
            if ans == "q":
                break
            if ans != "s":
                skipped += 1
                continue

        try:
            url = add_content_idea(idea)
            mark_save_processed(save["page_id"])
            print(f"  Guardada en Content Ideas DB -> {url}")
            processed += 1
        except Exception as exc:
            print(f"  [error] No se pudo guardar: {exc}", file=sys.stderr)
            skipped += 1

    print(f"\nResumen: {processed} ideas generadas, {skipped} omitidas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-transcribe", action="store_true")
    args = parser.parse_args()
    run(auto=args.auto, limit=args.limit, skip_transcribe=args.skip_transcribe)
