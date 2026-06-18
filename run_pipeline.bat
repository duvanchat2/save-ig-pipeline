@echo off
REM ============================================================
REM  Pipeline nocturno: sync → analyze → transform
REM  Se ejecuta via Windows Task Scheduler (tarea: IGSavesPipeline_Night)
REM ============================================================

SET PROJECT_DIR=C:\Users\duvan\OneDrive\Documentos\save IG
SET PYTHON=C:\Users\duvan\AppData\Local\Programs\Python\Python312\python.exe
SET LOG=%PROJECT_DIR%\pipeline.log

echo ======================================================== >> "%LOG%"
echo Pipeline iniciado: %DATE% %TIME% >> "%LOG%"

cd /d "%PROJECT_DIR%"

REM --- Fase 1: Sincronizar saves de Instagram ---
echo [1/3] Ejecutando sync.py... >> "%LOG%"
"%PYTHON%" "%PROJECT_DIR%\sync.py" >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo ERROR en sync.py - abortando pipeline >> "%LOG%"
    exit /b 1
)

REM --- Fase 2: Analizar saves nuevos con 4 filtros ---
echo [2/3] Ejecutando analyze.py --auto... >> "%LOG%"
"%PYTHON%" "%PROJECT_DIR%\analyze.py" --auto >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo WARN: analyze.py termino con error (puede ser que no haya saves nuevos) >> "%LOG%"
)

REM --- Fase 3: Transformar REPLICAR/ADAPTAR en ideas de contenido ---
echo [3/3] Ejecutando transform.py --auto... >> "%LOG%"
"%PYTHON%" "%PROJECT_DIR%\transform.py" --auto >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo WARN: transform.py termino con error (puede ser que no haya nada que procesar) >> "%LOG%"
)

echo Pipeline completado: %DATE% %TIME% >> "%LOG%"
echo ======================================================== >> "%LOG%"
