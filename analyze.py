"""
Fase 2 — Herramienta de datos para el Agente Analizador.

Modos:
  --fetch              Imprime JSON de saves pendientes (Verdict=SIN ANALIZAR)
  --transcribe URL     Transcribe el reel con AssemblyAI e imprime el texto
  --update PAGE_ID ... Escribe el veredicto en Notion

Uso manual (interactivo via Claude Code):
  /analyze-saves   ← el agente de Claude Code lee saves, analiza y llama --update

Uso autonomo (sin Claude):
  python analyze.py --auto --skip-transcribe
  (usa solo pre-filtro heuristico, sin LLM)
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone

from notion_db import get_unanalyzed_saves, update_save_verdict

# ── Pre-filtro heuristico (no requiere LLM) ───────────────────────────────────
_PAID_PATTERNS = [
    r'comenta\s+["\']?\w+["\']?', r'comment\s+["\']?\w+["\']?',
    r'te\s+(env[ii]o|mando|paso)\b', r"i'?ll\s+send\b",
    r'\bantes\s+del\b.*\d', r'\bbefore\s+\w+\s+\d+\b',
    r'\bsolo\s+hoy\b', r'\bonly\s+today\b', r'\blink\s+en\s+bio\b',
]
_NICHE_PATTERNS = [
    r'\b(ia|ai|gpt|claude|gemini|llm|modelo|model)\b',
    r'\b(automat|productividad|productivity|solopreneur|workflow)\b',
    r'\b(herramienta|tool|agent|prompt|api)\b',
    r'\b(emprendedor|founder|negocio\s+online|business)\b',
]
_VALID_FORMATS   = {"Short Reel <30s","Reel largo 30-90s","Carousel","Tutorial en pantalla","Lista","Historia","Antes-Despues","Comparativa","Demo de herramienta"}
_VALID_ENGAGEMENT = {"VIRAL","ALTO","NORMAL","BAJO","SIN DATOS"}


def _quick_prefilter(save: dict) -> tuple[bool, str]:
    text = (save.get("caption", "") or "").lower()
    paid  = sum(1 for p in _PAID_PATTERNS if re.search(p, text))
    niche = any(re.search(p, text) for p in _NICHE_PATTERNS)
    if paid >= 2 and not niche:
        return False, f"Pre-filtro: {paid} senales pagadas sin keywords de nicho -> DESCARTAR"
    return True, f"Pre-filtro: {paid} senal(es) pagadas, nicho={'SI' if niche else 'NO'} -> procede"


def _shortcode_from_url(url: str) -> str:
    m = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else ""


# ── Modo: --fetch ─────────────────────────────────────────────────────────────
def cmd_fetch():
    saves = get_unanalyzed_saves()
    print(json.dumps(saves, ensure_ascii=False, indent=2))


# ── Modo: --transcribe ────────────────────────────────────────────────────────
def cmd_transcribe(url: str):
    try:
        from assemblyai_transcriber import transcribe_reel
        transcript = transcribe_reel(url)
        print(transcript)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


# ── Modo: --update ────────────────────────────────────────────────────────────
def cmd_update(args):
    update_save_verdict(
        page_id        = args.page_id,
        verdict        = args.verdict,
        f1             = args.f1 or "DUDOSO",
        f2             = args.f2 or "SIN DATOS",
        f3             = args.f3 or "INCOMPATIBLE",
        f4             = args.f4 or "",
        report         = args.report or "",
        transcript     = args.transcript or "",
        hook           = args.hook or "",
        cuerpo         = args.cuerpo or "",
        cta            = args.cta or "",
        por_que_funciona = args.por_que_funciona or "",
        tipo_formato   = args.tipo_formato or "",
        engagement_level = args.engagement_level or "SIN DATOS",
    )
    print(f"OK: {args.page_id} -> {args.verdict}")


# ── Modo: --auto (sin LLM — solo pre-filtro) ──────────────────────────────────
def cmd_auto(limit: int = 0, skip_transcribe: bool = False):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{ts}] Modo auto (pre-filtro heuristico, sin LLM)...")

    saves = get_unanalyzed_saves()
    if limit:
        saves = saves[:limit]
    if not saves:
        print("No hay saves pendientes.")
        return

    for i, save in enumerate(saves, 1):
        print(f"\n[{i}/{len(saves)}] @{save.get('author','?')} -- {save.get('url','')}")
        proceed, reason = _quick_prefilter(save)
        print(f"  {reason}")

        if not proceed:
            update_save_verdict(
                save["page_id"], "DESCARTAR", "PAGADO", "SIN DATOS", "INCOMPATIBLE",
                "Lead magnet puro.", reason,
                engagement_level="SIN DATOS",
            )
            print("  -> DESCARTAR (guardado)")
            continue

        transcript = ""
        if not skip_transcribe and save.get("url"):
            try:
                from assemblyai_transcriber import transcribe_reel
                transcript = transcribe_reel(save["url"])
            except Exception as e:
                print(f"  [transcribe] {e}", file=sys.stderr)

        # Sin LLM: marcar como DUDOSO para revision manual posterior
        update_save_verdict(
            save["page_id"], "SIN ANALIZAR", "DUDOSO", "SIN DATOS", "ADAPTABLE",
            "", f"Pre-filtro: {reason}. Pendiente de analisis con Claude Code (/analyze-saves).",
            transcript=transcript,
            engagement_level="SIN DATOS",
        )
        print("  -> pendiente de analisis con Claude Code")

    print("\nAuto completado. Ejecuta /analyze-saves en Claude Code para el analisis completo.")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode")

    sub.add_parser("fetch", help="Imprime saves pendientes como JSON")

    tr = sub.add_parser("transcribe", help="Transcribe un reel")
    tr.add_argument("url")

    up = sub.add_parser("update", help="Escribe veredicto en Notion")
    up.add_argument("--page-id",          required=True)
    up.add_argument("--verdict",          required=True, choices=["REPLICAR","ADAPTAR","SOLO ESTRUCTURA","DESCARTAR"])
    up.add_argument("--f1",               default="")
    up.add_argument("--f2",               default="")
    up.add_argument("--f3",               default="")
    up.add_argument("--f4",               default="")
    up.add_argument("--report",           default="")
    up.add_argument("--transcript",       default="")
    up.add_argument("--hook",             default="")
    up.add_argument("--cuerpo",           default="")
    up.add_argument("--cta",              default="")
    up.add_argument("--por-que-funciona", default="")
    up.add_argument("--tipo-formato",     default="")
    up.add_argument("--engagement-level", default="SIN DATOS")

    # Modo legado para la automatizacion nocturna (sin LLM)
    parser.add_argument("--auto",            action="store_true")
    parser.add_argument("--limit",           type=int, default=0)
    parser.add_argument("--skip-transcribe", action="store_true")

    args = parser.parse_args()

    if args.mode == "fetch":
        cmd_fetch()
    elif args.mode == "transcribe":
        cmd_transcribe(args.url)
    elif args.mode == "update":
        cmd_update(args)
    elif args.auto:
        cmd_auto(limit=args.limit, skip_transcribe=args.skip_transcribe)
    else:
        parser.print_help()
