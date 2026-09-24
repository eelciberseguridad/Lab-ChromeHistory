from __future__ import annotations

import ctypes
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from analyzer import analyze, generate_html_report, regenerate_outputs, sha256_file

BASE = Path(__file__).resolve().parent
EVIDENCIA = BASE / "evidencia"
RESULTADOS = BASE / "resultados"
USE_COLOR = False


def enable_vt():
    global USE_COLOR
    if os.name != "nt":
        USE_COLOR = True
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            USE_COLOR = True
    except Exception:
        USE_COLOR = False


def c(code, text):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="-", width=108):
    print(char * width)


def banner(section="", detail=""):
    clear()
    line("=", 108)
    print(c("97", "  EEL CIBERSEGURIDAD"))
    print(c("96", "  ANALIZADOR DE HISTORIAL DE NAVEGACIÓN // WINDOWS"))
    print(c("90", "  eelciberseguridad@gmail.com"))
    line("=", 108)
    if section:
        print(c("97", f"  {section}"))
    if detail:
        print(c("90", f"  {detail}"))
    if section:
        line("-", 108)
    print()


def pause(text="Presione ENTER para continuar..."):
    input("\n" + c("90", text))


def ok(text):
    print(c("92", f"[ OK ] {text}"))


def warn(text):
    print(c("93", f"[ !  ] {text}"))


def info(text):
    print(c("96", f"[ :: ] {text}"))


def fail(text):
    print(c("91", f"[ERR ] {text}"))


def is_windows():
    return os.name == "nt"


def open_path(path):
    path = Path(path).resolve()
    if is_windows():
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])



def open_report(path):
    """Abre un informe HTML sin bloquear la consola."""
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() != ".html":
        return open_path(path)

    if is_windows():
        try:
            os.startfile(str(path))
            return
        except OSError:
            pass

    opened = webbrowser.open_new_tab(path.as_uri())
    if not opened:
        open_path(path)



def human_size(n):
    value = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024


def format_utc(value):
    if not value:
        return "No disponible"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%d/%m/%Y · %H:%M:%S UTC")
    except Exception:
        return str(value)


def chrome_base():
    local = os.environ.get("LOCALAPPDATA")
    return Path(local) / "Google" / "Chrome" / "User Data" if local else None


def find_profiles():
    base = chrome_base()
    if not base or not base.exists():
        return []
    profiles = []
    for p in base.iterdir():
        h = p / "History"
        if p.is_dir() and h.exists():
            profiles.append(p)
    return sorted(profiles, key=lambda p: p.name.lower())


def chrome_running():
    if not is_windows():
        return False
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
            capture_output=True, text=True, errors="ignore"
        )
        return "chrome.exe" in r.stdout.lower()
    except Exception:
        return False


def detect_and_choose_profile():
    banner(
        "01 · DETECCIÓN DE PERFILES",
        "Localizando bases History de perfiles compatibles"
    )
    info(f"Ruta examinada: {chrome_base()}")
    print()

    profiles = find_profiles()
    if not profiles:
        fail("No se encontraron perfiles con archivo History.")
        print()
        print("Puede verificar manualmente el perfil activo desde:")
        print(c("96", "  chrome://version"))
        print("y revisar el campo:")
        print(c("96", "  Profile Path"))
        pause()
        return None

    ok(f"Se encontraron {len(profiles)} perfil(es).")
    print()

    for i, p in enumerate(profiles, 1):
        h = p / "History"
        print(c("92", f"  [{i}] {p.name}"))
        print(f"      Ruta    : {p}")
        print(f"      History : {human_size(h.stat().st_size)}")
        print()

    while True:
        v = input(c("97", "Seleccione el perfil que desea analizar o M para cancelar: ")).strip().lower()
        if v == "m":
            return None
        try:
            idx = int(v) - 1
            if 0 <= idx < len(profiles):
                return profiles[idx]
        except ValueError:
            pass
        warn("Opción inválida.")


def ensure_chrome_closed():
    while chrome_running():
        warn("El navegador compatible está abierto.")
        print()
        print("Para realizar una copia estable, cierre todas las ventanas del navegador.")
        print("El programa no finalizará procesos automáticamente.")
        v = input("\nCierre Chrome y presione ENTER para comprobar nuevamente, o M para cancelar: ").strip().lower()
        if v == "m":
            return False
        print()
    ok("El navegador no está en ejecución.")
    return True


def acquire_profile(profile):
    banner(
        "02 · ADQUISICIÓN",
        f"Perfil seleccionado: {profile.name}"
    )
    print("Se creará una copia de trabajo. El análisis no se ejecutará sobre el archivo original.")
    print()

    if not ensure_chrome_closed():
        return None

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = EVIDENCIA / f"{profile.name}_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    log = [
        "EEL CIBERSEGURIDAD",
        "ANALIZADOR DE HISTORIAL DE NAVEGACIÓN",
        "REGISTRO DE ADQUISICIÓN",
        "=" * 72,
        f"Perfil: {profile}",
        f"Fecha UTC: {datetime.now(timezone.utc).isoformat()}",
        ""
    ]

    history_copy = None
    unstable = False

    print()
    info("Adquiriendo registros de navegación...")
    print()

    for name in ["History", "History-wal", "History-shm"]:
        src = profile / name
        if not src.exists():
            continue
        dst = dest / name
        try:
            before = sha256_file(src)
            shutil.copy2(src, dst)
            copied = sha256_file(dst)
            after = sha256_file(src)
            stable = before == copied == after
            unstable = unstable or not stable

            if name == "History":
                history_copy = dst

            ok(name)
            print(c("90", f"       SHA-256 {copied}"))

            log.extend([
                f"Archivo: {name}",
                f"Origen: {src}",
                f"Copia: {dst}",
                f"SHA256 origen antes: {before}",
                f"SHA256 copia: {copied}",
                f"SHA256 origen después: {after}",
                f"Coincidencia estable: {'SI' if stable else 'NO'}",
                ""
            ])
        except Exception as exc:
            fail(f"{name}: {exc}")
            log.extend([f"ERROR {name}: {exc}", ""])

    (dest / "adquisicion.txt").write_text("\n".join(log), encoding="utf-8")

    print()
    line()
    if not history_copy:
        fail("No se pudo adquirir el archivo History.")
        pause()
        return None

    ok("COPIA ADQUIRIDA")
    print(f"  Carpeta: {dest}")

    if unstable:
        warn("Algún hash cambió durante la copia. Se recomienda repetir la adquisición.")
        pause()
        return None

    ok("Integridad consistente durante la copia.")
    pause("Presione ENTER para iniciar automáticamente el análisis...")
    return history_copy


def analyze_copy(history_copy):
    banner(
        "03 · ANÁLISIS SQLITE",
        "Extracción de registros de navegación"
    )
    print(f"Evidencia:\n  {history_copy}\n")
    info("Abriendo la copia en modo lectura.")
    info("Detectando tablas y campos disponibles.")
    info("Reconstruyendo timeline, búsquedas, descargas y relaciones de navegación.")
    print()

    out = RESULTADOS / history_copy.parent.name

    try:
        data = analyze(history_copy, out)
        generate_html_report(data, out / "CENTRO_DE_CONSULTA.html")
    except sqlite3.DatabaseError as exc:
        fail("SQLite no pudo interpretar la base.")
        print(exc)
        pause()
        return None
    except Exception as exc:
        fail(str(exc))
        pause()
        return None

    r = data["resumen"]
    m = data["metadata"]

    ok("ANÁLISIS FINALIZADO")
    print()
    line()
    print(c("96", "  RESUMEN DE HALLAZGOS"))
    line()
    print(f"  URLs recuperadas         {c('92', str(r['urls']))}")
    print(f"  Eventos de visita        {c('92', str(r['visitas']))}")
    print(f"  Dominios diferentes      {c('92', str(r['dominios']))}")
    print(f"  Búsquedas identificadas  {c('92', str(r['busquedas']))}")
    print(f"  Descargas registradas    {c('92', str(r['descargas']))}")
    print(f"  URLs con typed_count     {c('92', str(r['urls_escritas']))}")
    print()
    print(f"  Primer evento UTC : {format_utc(m['primer_evento_utc'])}")
    print(f"  Último evento UTC : {format_utc(m['ultimo_evento_utc'])}")
    print()
    print(f"  Resultados: {out}")
    pause("Presione ENTER para abrir las opciones del análisis...")
    return out


def analysis_folders():
    items = []
    for p in RESULTADOS.rglob("analisis.json"):
        try:
            items.append((p.stat().st_mtime, p.parent))
        except OSError:
            pass
    return [p for _, p in sorted(items, reverse=True)]




def refresh_generated_files(folder):
    folder = Path(folder)
    source = folder / "analisis.json"
    if not source.exists():
        return False, "No se encontró analisis.json."
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        regenerate_outputs(data, folder)
        generate_html_report(data, folder / "CENTRO_DE_CONSULTA.html")
        return True, ""
    except Exception as exc:
        return False, str(exc)


def generated_file_candidates(folder):
    folder = Path(folder)
    return [
        ("Centro de consulta", folder / "CENTRO_DE_CONSULTA.html"),
        ("Resumen", folder / "RESUMEN.html"),
        ("Línea de tiempo", folder / "LINEA_DE_TIEMPO.html"),
        ("Páginas y URLs", folder / "PAGINAS_Y_URLS.html"),
        ("Dominios", folder / "DOMINIOS.html"),
        ("Tipos de navegación", folder / "TIPOS_DE_NAVEGACION.html"),
        ("Origen de visitas", folder / "ORIGEN_DE_VISITAS.html"),
        ("Búsquedas", folder / "BUSQUEDAS.html"),
        ("Descargas", folder / "DESCARGAS.html"),
    ]


def consult_folder(folder):
    """Consulta los resultados de un análisis sin pausas entre aperturas."""
    folder = Path(folder)
    notice = ""

    reports = generated_file_candidates(folder)
    source = folder / "analisis.json"

    needs_refresh = any(not path.exists() for _, path in reports)

    if source.exists() and not needs_refresh:
        try:
            source_mtime = source.stat().st_mtime
            needs_refresh = any(
                path.stat().st_mtime < source_mtime
                for _, path in reports
            )
        except OSError:
            needs_refresh = True

    if needs_refresh:
        success, message = refresh_generated_files(folder)
        if not success:
            notice = f"No se pudieron actualizar todos los resultados: {message}"

    while True:
        banner("RESULTADOS GENERADOS", folder.name)
        reports = generated_file_candidates(folder)

        if notice:
            info(notice)
            print()
            notice = ""

        for i, (name, path) in enumerate(reports, 1):
            state = c("92", "DISPONIBLE") if path.exists() else c("91", "NO DISPONIBLE")
            print(c("92", f"  [{i}] {name}"))
            print(c("90", f"      {path.name} · ") + state)

        print()
        print(c("97", "  [M] Volver"))
        print()

        value = input(
            "Seleccione un resultado para abrir o M para volver: "
        ).strip().lower()

        if value == "m":
            return

        try:
            idx = int(value) - 1
        except ValueError:
            notice = "Opción inválida."
            continue

        if not (0 <= idx < len(reports)):
            notice = "Opción inválida."
            continue

        name, path = reports[idx]

        if not path.exists():
            success, message = refresh_generated_files(folder)
            if not success or not path.exists():
                notice = (
                    f"No se pudo generar {name}: "
                    f"{message or 'archivo no disponible'}"
                )
                continue

        try:
            open_report(path)
            notice = (
                f"{name} abierto. "
                "Elegí otro número o M para volver."
            )
        except Exception as exc:
            notice = f"No se pudo abrir {name}: {exc}"

        # No pause(): el menú queda listo de inmediato.



def post_analysis_menu(result_dir):
    while True:
        banner("ANÁLISIS COMPLETADO", result_dir.name)
        print(c("92", "  EVIDENCIA PROCESADA CORRECTAMENTE"))
        print()
        print("  [1] Consultar resultados de este análisis")
        print("  [2] Abrir carpeta de este análisis")
        print("  [3] Volver a la pantalla principal")
        print()
        v = input(c("97", "Seleccione una opción: ")).strip()

        if v == "1":
            consult_folder(result_dir)
        elif v == "2":
            open_path(result_dir)
        elif v == "3":
            return
        else:
            warn("Opción inválida.")
            pause()

def new_analysis_wizard():
    profile = detect_and_choose_profile()
    if not profile:
        return

    history = acquire_profile(profile)
    if not history:
        return

    result_dir = analyze_copy(history)
    if not result_dir:
        return

    post_analysis_menu(result_dir)



def consult_reports():
    """Consulta análisis anteriores y todos sus resultados HTML."""
    while True:
        banner(
            "ANÁLISIS GENERADOS",
            "Seleccione un análisis para consultar sus resultados"
        )

        items = analysis_folders()
        if not items:
            warn("Todavía no hay análisis generados.")
            pause()
            return

        for i, folder in enumerate(items, 1):
            analysis_json = folder / "analisis.json"
            try:
                modified = datetime.fromtimestamp(analysis_json.stat().st_mtime).strftime("%d/%m/%Y · %H:%M")
            except OSError:
                modified = "Fecha no disponible"

            ready = sum(1 for _, path in generated_file_candidates(folder) if path.exists())
            print(c("92", f"  [{i}] {folder.name}"))
            print(c("90", f"      Fecha: {modified} · Resultados disponibles: {ready}/9"))
            print()

        print(c("97", "  [M] Volver"))
        print()
        value = input("Seleccione un análisis o M para volver: ").strip().lower()

        if value == "m":
            return

        try:
            idx = int(value) - 1
        except ValueError:
            continue

        if not (0 <= idx < len(items)):
            continue

        consult_folder(items[idx])


def main():
    enable_vt()
    EVIDENCIA.mkdir(exist_ok=True)
    RESULTADOS.mkdir(exist_ok=True)

    while True:
        banner(
            "PANTALLA PRINCIPAL",
            "Historial del navegador · SQLite · SHA-256 · Resultados HTML"
        )
        print(c("92", "  [1] DETECTAR PERFILES COMPATIBLES"))
        print(c("90", "      Busca perfiles compatibles e inicia la adquisición y el análisis."))
        print()
        print(c("96", "  [2] CONSULTAR ANÁLISIS GENERADOS"))
        print(c("90", "      Elegí un análisis y abrí cualquiera de sus nueve resultados HTML."))
        print()
        print()
        print(c("90", "  [0] SALIR"))
        print()
        line()
        v = input(c("97", "Seleccione una opción: ")).strip()

        if v == "1":
            new_analysis_wizard()
        elif v == "2":
            consult_reports()
        elif v == "0":
            banner("PROGRAMA FINALIZADO")
            print("La evidencia original no fue modificada por el analizador.")
            break
        else:
            warn("Opción inválida.")
            pause()


if __name__ == "__main__":
    main()
