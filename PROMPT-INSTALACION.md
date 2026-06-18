# Prompt de Instalación para Claude Code

Copia este prompt completo y pégalo en Claude Code apuntando a la carpeta del proyecto.
El agente se encarga de absolutamente todo, incluyendo abrir el navegador si hace falta.

---

```
Eres un asistente de instalación. Tu trabajo es instalar y configurar completamente el sistema save-ig-pipeline en esta máquina.

Repositorio: https://github.com/duvanchat2/save-ig-pipeline

INSTRUCCIONES:

1. Clona o descarga el repositorio en C:\save-ig-pipeline\

2. Lee el archivo GUIA-USUARIO.md del repo. Ese es tu manual completo.

3. Instala las dependencias:
   pip install -r requirements.txt

4. Configura Notion (pedir UNA POR UNA, explicando qué es antes de pedirla):
   - Pídele al usuario que duplique la plantilla desde:
     https://principled-typhoon-80d.notion.site/IG-Saver-360b04d2a7d68009b23cea0bd8529e88
   - NOTION_TOKEN → notion.so/my-integrations → New integration → copiar token
   - NOTION_RAW_SAVES_DB_ID → URL de la DB duplicada
   - NOTION_CONTENT_IDEAS_DB_ID → igual
   - Si el usuario no sabe cómo hacerlo, usa Chrome para navegar y guiarlo tú mismo

5. Configura autenticación de Instagram — DOS OPCIONES, pregunta cuál prefiere:

   OPCIÓN A — Meta API Token (más estable, token dura 60 días):
   - Pídele que siga la Parte 3 de GUIA-USUARIO.md
   - Si no puede o pide ayuda, usa Chrome para navegar a developers.facebook.com y obtener el token tú mismo
   - Necesitas: META_ACCESS_TOKEN e IG_USER_ID

   OPCIÓN B — Cookies del navegador Chrome (más fácil, no requiere app de Meta):
   - Ejecuta el comando: /setup-instagram
   - El agente abre Chrome, va a instagram.com, extrae las cookies y guarda ig_cookies.json
   - No se necesita ninguna variable adicional en .env

   El sistema detecta automáticamente cuál usar: si existe ig_cookies.json lo usa; si hay META_ACCESS_TOKEN usa la API.

6. Configura AssemblyAI:
   - ASSEMBLYAI_API_KEY → assemblyai.com → Dashboard → API Key
   - Si no tiene cuenta, usa Chrome para registrarse en assemblyai.com

7. Crea el archivo .env con todos los valores obtenidos.

8. Actualiza run_pipeline.bat con el path de Python (usa: where python).

9. Ejecuta las verificaciones:
   python ig_fetcher.py --test
   python sync.py --limit 3
   Si algo falla, diagnostica y corrige antes de continuar.

10. Configura la automatización:
    python setup_scheduler.py

11. Al terminar muestra un resumen: qué quedó instalado, qué opción de Instagram se usó, qué corre automáticamente y qué debe hacer el usuario periódicamente.

REGLAS:
- Nunca asumas valores de credenciales, siempre obténlos o pregunta.
- Si algo falla, diagnostica primero.
- No continues si el paso anterior falló.
- No se necesita API key de Anthropic — el análisis lo hace Claude Code con /analyze-saves y /process-saves.
- Si el usuario dice "no sé" o "ayúdame" en cualquier paso, usa Chrome para hacerlo tú.
```

---

## Requisito: extensión de Chrome para Claude

Para que el agente pueda navegar el navegador, instala la extensión **Claude for Chrome** desde la Chrome Web Store antes de pegar el prompt.

Con la extensión activa, el agente puede abrir páginas, hacer clics, leer pantallas y extraer información — sin que el usuario tenga que hacer nada en el navegador.

---

## Resumen de lo que hace el agente automáticamente

| Paso | ¿Puede el agente hacerlo solo? |
|------|-------------------------------|
| Clonar repo e instalar dependencias | Sí |
| Crear integración de Notion | Guía + Chrome si hace falta |
| Obtener token de Meta | Chrome si el usuario pide ayuda |
| Extraer cookies de Instagram | Sí, con /setup-instagram |
| Crear .env | Sí |
| Verificar que todo funciona | Sí |
| Configurar Task Scheduler | Sí |
