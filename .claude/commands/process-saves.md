# Process Instagram Saves

Transforma los posts guardados de Instagram (Raw Saves en Notion) en borradores
de contenido listos para producción (Content Ideas en Notion).

## Lo que hace este comando

1. Consulta Notion Raw Saves DB y obtiene entradas con `Processed = false`
2. Para cada save, usa Claude AI para generar:
   - Nombre/título de la idea
   - Pilar de contenido asignado (Outreach / Proof / Tools / Process)
   - 3 hooks (curiosidad, dolor, resultado)
   - Outline estructurado: Hook → Body → CTA
   - Formato y plataformas recomendadas
3. Presenta cada idea para revisión antes de guardar (o usa `--auto` para aprobar todo)
4. Escribe las ideas aprobadas en Content Ideas DB y marca el save como procesado

## Uso

```bash
# Modo interactivo (recomendado): revisa idea por idea
python transform.py

# Aprobar todo automáticamente
python transform.py --auto

# Procesar solo los primeros N saves
python transform.py --limit 5

# Combinar: auto + límite
python transform.py --auto --limit 10
```

## Requisitos previos

- Archivo `.env` configurado con `NOTION_TOKEN`, `NOTION_RAW_SAVES_DB_ID`,
  `NOTION_CONTENT_IDEAS_DB_ID`, y `ANTHROPIC_API_KEY`
- Haber ejecutado `python sync.py` al menos una vez para tener Raw Saves en Notion

## Notas

- El nicho objetivo está configurado en `.env` como `CONTENT_NICHE`
- Los pilares están en `CONTENT_PILLARS`
- Si Claude falla en un save (error de API), ese save se omite y continúa con el siguiente

$ARGUMENTS
