# Prompt de Instalación para Claude Code

Copia este prompt completo y pégalo en Claude Code apuntando a la carpeta del proyecto.
Claude Code se encargará de absolutamente todo.

---

```
Eres un asistente de instalación. Tu trabajo es instalar y configurar completamente el sistema save-ig-pipeline en esta máquina.

Repositorio: https://github.com/duvanchat2/save-ig-pipeline

INSTRUCCIONES:

1. Clona o descarga el repositorio en C:\save-ig-pipeline\

2. Lee el archivo GUIA-USUARIO.md del repo. Ese es tu manual completo de instalación. Síguelo al pie de la letra.

3. Instala las dependencias con pip install -r requirements.txt

4. Pídeme las siguientes credenciales UNA POR UNA (no todas juntas). Para cada una explícame en 1 línea qué es y dónde la encuentro antes de pedirla:
   - NOTION_TOKEN
   - NOTION_RAW_SAVES_DB_ID (después de duplicar la plantilla)
   - NOTION_CONTENT_IDEAS_DB_ID
   - META_ACCESS_TOKEN
   - IG_USER_ID
   - ASSEMBLYAI_API_KEY

5. Con los valores que te dé, crea el archivo .env automáticamente.

6. Actualiza run_pipeline.bat con el path correcto de Python en esta máquina.

7. Ejecuta las verificaciones de la Parte 6 de GUIA-USUARIO.md y dime si cada una pasa o falla. Si falla, dime exactamente qué hacer para corregirlo.

8. Configura el Task Scheduler ejecutando: python setup_scheduler.py

9. Al terminar dame un resumen de qué quedó instalado, qué tareas automáticas están activas y qué debo hacer cada 60 días (renovar el token de Meta).

REGLAS:
- No asumas ningún valor por defecto para las credenciales, siempre pregúntame.
- Si algo falla, diagnostica el error antes de pedirme que haga algo.
- No continues al siguiente paso si el anterior falló.
- La plantilla de Notion para duplicar está en: https://principled-typhoon-80d.notion.site/IG-Saver-360b04d2a7d68009b23cea0bd8529e88
- No necesito API key de Anthropic — el análisis lo hace Claude Code directamente con /analyze-saves y /process-saves.
```

---

## Lo que el usuario hace manualmente (el agente no puede abrir el navegador)

Antes de pegar el prompt, el usuario debe tener listos:

1. **Token de Meta** — seguir Parte 3 de GUIA-USUARIO.md para crearlo
2. **Plantilla de Notion duplicada** — abrir el link de arriba y hacer click en "Duplicate"
3. **API key de AssemblyAI** — registrarse en assemblyai.com (gratis)

Todo lo demás lo hace el agente.
