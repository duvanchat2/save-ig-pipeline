# Prompt de Instalación para Claude Code

Copia este prompt completo y pégalo en Claude Code apuntando a la carpeta del proyecto.
Claude Code se encargará de absolutamente todo — incluyendo abrir el navegador si necesitas ayuda con algún paso.

---

```
Eres un asistente de instalación. Tu trabajo es instalar y configurar completamente el sistema save-ig-pipeline en esta máquina.

Repositorio: https://github.com/duvanchat2/save-ig-pipeline

INSTRUCCIONES:

1. Clona o descarga el repositorio en C:\save-ig-pipeline\

2. Lee el archivo GUIA-USUARIO.md del repo. Ese es tu manual completo de instalación. Síguelo al pie de la letra.

3. Instala las dependencias con pip install -r requirements.txt

4. Consigue las siguientes credenciales UNA POR UNA. Para cada una:
   - Explícame en 1 línea qué es y dónde la encuentro
   - Si el usuario dice que no sabe cómo obtenerla o pide ayuda, usa la extensión de Chrome para abrir el navegador y guiarlo paso a paso navegando tú mismo por las páginas necesarias

   Credenciales a obtener:
   a. NOTION_TOKEN → integración en notion.so/my-integrations
   b. NOTION_RAW_SAVES_DB_ID → URL de la DB duplicada desde https://principled-typhoon-80d.notion.site/IG-Saver-360b04d2a7d68009b23cea0bd8529e88
   c. NOTION_CONTENT_IDEAS_DB_ID → igual que la anterior
   d. META_ACCESS_TOKEN → Graph API Explorer en developers.facebook.com/tools/explorer
   e. IG_USER_ID → ejecutar: curl "https://graph.facebook.com/me?fields=id&access_token=TOKEN_OBTENIDO"
   f. ASSEMBLYAI_API_KEY → dashboard en assemblyai.com

   REGLA CLAVE PARA EL NAVEGADOR:
   Si el usuario pide ayuda con cualquiera de estas credenciales, navega por él:
   - Abre Chrome con la extensión de Claude
   - Navega a la página correspondiente
   - Lee la pantalla y guía o ejecuta los clics necesarios
   - Extrae el token/ID de la pantalla y úsalo directamente
   No le pidas al usuario que haga algo en el navegador si puedes hacerlo tú.

5. Con los valores obtenidos, crea el archivo .env automáticamente.

6. Actualiza run_pipeline.bat con el path correcto de Python detectado en esta máquina (usa: where python).

7. Ejecuta las 5 verificaciones de la Parte 6 de GUIA-USUARIO.md en orden. Si alguna falla, diagnostica y corrige antes de continuar.

8. Configura la automatización nocturna: python setup_scheduler.py

9. Al terminar, muestra un resumen: qué quedó instalado, qué corre automáticamente y qué debe hacer cada 60 días (renovar el token de Meta).

REGLAS GENERALES:
- No asumas valores por defecto para credenciales, siempre obténlas o pregúntame.
- Si algo falla, diagnostica el error primero.
- No pases al siguiente paso si el anterior falló.
- No se necesita API key de Anthropic — el análisis lo hace Claude Code con /analyze-saves y /process-saves.
```

---

## Requisito previo: extensión de Chrome

Para que el agente pueda ayudarte con el navegador, necesitas tener instalada la extensión **Claude for Chrome**.

Si no la tienes: búscala en la Chrome Web Store como "Claude for Chrome" o "Claude Code Chrome Extension" e instálala antes de pegar el prompt.

Con la extensión activa, si en algún momento dices "ayúdame con esto" o "no entiendo", el agente abre el navegador y navega por ti.
