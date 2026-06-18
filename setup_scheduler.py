"""
Crea tareas en Windows Task Scheduler:
  - Dos syncs diarios (8 AM y 8 PM) — solo sync.py
  - Un pipeline nocturno (2 AM) — sync + analyze + transform completo

Uso (ejecutar como Administrador o desde PowerShell elevado):
  python setup_scheduler.py              # Crea/actualiza todas las tareas
  python setup_scheduler.py --remove    # Elimina las tareas
  python setup_scheduler.py --status    # Muestra estado actual
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
PYTHON_PATH = sys.executable
BAT_PATH = PROJECT_DIR / "run_pipeline.bat"

# Tareas de sync rápido (solo sincronización)
SYNC_TASKS = [
    ("InstagramSavesSync_AM", "08:00"),
    ("InstagramSavesSync_PM", "20:00"),
]

# Tarea de pipeline completo (sync + analyze + transform)
PIPELINE_TASK = ("IGSavesPipeline_Night", "02:00")

ALL_TASK_NAMES = [t[0] for t in SYNC_TASKS] + [PIPELINE_TASK[0]]


def _schtasks(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["schtasks"] + list(args),
        capture_output=True,
        text=True,
    )


def create_tasks():
    sync_script = PROJECT_DIR / "sync.py"

    # Crear tareas de sync diario
    for task_name, start_time in SYNC_TASKS:
        cmd = f'"{PYTHON_PATH}" "{sync_script}"'
        result = _schtasks(
            "/create", "/tn", task_name,
            "/tr", cmd,
            "/sc", "daily", "/st", start_time,
            "/f",
        )
        status = "OK" if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"
        print(f"  Sync {start_time}  [{task_name}]: {status}")

    # Crear tarea de pipeline nocturno (llama al .bat)
    task_name, start_time = PIPELINE_TASK
    result = _schtasks(
        "/create", "/tn", task_name,
        "/tr", f'"{BAT_PATH}"',
        "/sc", "daily", "/st", start_time,
        "/f",
    )
    status = "OK" if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"
    print(f"  Pipeline {start_time} [{task_name}]: {status}")
    print()
    print(f"  Log nocturno: {PROJECT_DIR / 'pipeline.log'}")


def remove_tasks():
    for task_name in ALL_TASK_NAMES:
        result = _schtasks("/delete", "/tn", task_name, "/f")
        status = "eliminada" if result.returncode == 0 else f"no encontrada ({result.stderr.strip()})"
        print(f"  [{task_name}]: {status}")


def show_status():
    for task_name in ALL_TASK_NAMES:
        result = _schtasks("/query", "/tn", task_name, "/fo", "LIST")
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"  '{task_name}' no encontrada\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configura Windows Task Scheduler")
    parser.add_argument("--remove", action="store_true", help="Eliminar todas las tareas")
    parser.add_argument("--status", action="store_true", help="Ver estado de tareas")
    args = parser.parse_args()

    if args.remove:
        print("Eliminando tareas...")
        remove_tasks()
    elif args.status:
        show_status()
    else:
        print("Creando tareas en Windows Task Scheduler...")
        print(f"  Proyecto: {PROJECT_DIR}")
        print(f"  Python:   {PYTHON_PATH}")
        print()
        create_tasks()
        print()
        print("Verifica con: python setup_scheduler.py --status")
