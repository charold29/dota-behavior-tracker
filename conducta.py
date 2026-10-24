"""
conducta.py - Guarda un historial de tu Behavior Score de Dota 2.

Valve no guarda historial: solo deja el ultimo resumen en un archivo local
(latest_conduct_*.txt). Este script lo lee y anota cada resumen nuevo en un CSV.

Uso:
  python conducta.py                          registra el resumen actual (si es nuevo)
  python conducta.py ver                      muestra el archivo de Valve y como se interpreto
  python conducta.py agregar 7800             agrega un valor a mano (hoy)
  python conducta.py agregar 7500 --fecha 2026-09-01
  python conducta.py grafica                  dibuja la evolucion (requiere matplotlib)
"""
import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

from resumen_conducta import FormatoInvalidoError, ResumenConducta

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "historial_conducta.csv"
PNG_PATH = BASE / "historial_conducta.png"
CAMPOS = ["fecha_registro", "fecha_archivo", "behavior_score", "behavior_anterior",
          "rating", "origen", "seq_num", "datos"]
RUTA_CFG = Path("steamapps") / "common" / "dota 2 beta" / "game" / "dota" / "cfg"


# ---------------------------------------------------------------- Steam ----

def carpetas_steam():
    """Carpeta principal de Steam + bibliotecas extra (otros discos/carpetas)."""
    import winreg  # solo existe en Windows; se importa aqui para no romper los tests

    rutas = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            rutas.append(Path(winreg.QueryValueEx(k, "SteamPath")[0]))
    except OSError:
        pass
    rutas += [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam")]

    extra = []
    for r in rutas:
        vdf = r / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            texto = vdf.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'"path"\s+"([^"]+)"', texto):
                extra.append(Path(m.group(1).replace("\\\\", "\\")))

    vistos, unicas = set(), []
    for r in rutas + extra:
        clave = str(r).lower()
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(r)
    return unicas


def buscar_archivo():
    candidatos = []
    for steam in carpetas_steam():
        cfg = steam / RUTA_CFG
        if cfg.is_dir():
            candidatos += list(cfg.glob("latest_conduct_*.txt"))
    if not candidatos:
        return None
    return max(candidatos, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------- CSV ------

def leer_historial():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def agregar_fila(fila):
    nuevo = not CSV_PATH.exists()
    with CSV_PATH.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


# ---------------------------------------------------------------- comandos -

def cmd_registrar(_args):
    archivo = buscar_archivo()
    if archivo is None:
        print("No encontre latest_conduct_*.txt. Abre Dota 2 al menos una vez "
              "y revisa que el juego este instalado en Steam.")
        return 1

    try:
        resumen = ResumenConducta.desde_archivo(archivo)
    except FormatoInvalidoError as e:
        print(f"No pude leer el resumen: {e}")
        return 1

    ya_registrados = {r["seq_num"] for r in leer_historial() if r["origen"] == "archivo"}
    if str(resumen.seq_num) in ya_registrados:
        print(f"Sin cambios (resumen #{resumen.seq_num} ya registrado, score {resumen.raw_behavior_score}).")
        return 0

    agregar_fila(resumen.a_fila(fecha_registro=datetime.now().astimezone()))
    cambio = f" ({resumen.cambio:+d} vs anterior)" if resumen.cambio is not None else ""
    fecha_local = resumen.fecha.astimezone()
    print(f"Registrado resumen #{resumen.seq_num} del {fecha_local:%d/%m/%Y}: "
          f"{resumen.raw_behavior_score}{cambio}")
    return 0


def cmd_ver(_args):
    archivo = buscar_archivo()
    if archivo is None:
        print("No encontre el archivo de conducta.")
        return 1
    print(f"Archivo: {archivo}\n")
    print(archivo.read_text(encoding="utf-8", errors="ignore"))
    try:
        print("\nInterpretado:", ResumenConducta.desde_archivo(archivo))
    except FormatoInvalidoError as e:
        print(f"\nNo pude interpretarlo: {e}")
    return 0


def cmd_agregar(args):
    fecha = args.fecha or datetime.now().strftime("%Y-%m-%d")
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").astimezone()
    except ValueError:
        print("Fecha invalida, usa el formato AAAA-MM-DD.")
        return 1
    agregar_fila({
        "fecha_registro": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fecha_archivo": fecha_dt.isoformat(timespec="seconds"),
        "behavior_score": str(args.valor),
        "behavior_anterior": "",
        "rating": "",
        "origen": "manual",
        "seq_num": "",
        "datos": "",
    })
    print(f"Agregado {args.valor} con fecha {fecha}.")
    return 0


def _fecha_local(texto):
    fecha = datetime.fromisoformat(texto)
    return fecha.astimezone()  # convierte a hora local (y vuelve "aware" las fechas sin zona)


def cmd_grafica(_args):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Falta matplotlib. Instalalo con: pip install matplotlib")
        return 1

    puntos = []
    for r in leer_historial():
        if r["behavior_score"]:
            fecha = _fecha_local(r["fecha_archivo"] or r["fecha_registro"])
            puntos.append((fecha.replace(tzinfo=None), float(r["behavior_score"])))
    if not puntos:
        print("Todavia no hay valores con behavior score en el historial.")
        return 1
    puntos.sort()
    x, y = zip(*puntos)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_title("Behavior Score - Dota 2")
    ax.set_ylabel("Puntos")
    ax.set_ylim(0, 12000)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=120)
    print(f"Grafica guardada en {PNG_PATH}")
    plt.show()
    return 0


def main():
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="Historial de Behavior Score de Dota 2")
    sub = p.add_subparsers(dest="comando")
    sub.add_parser("ver")
    sub.add_parser("grafica")
    a = sub.add_parser("agregar")
    a.add_argument("valor", type=int)
    a.add_argument("--fecha", help="AAAA-MM-DD (por defecto hoy)")

    args = p.parse_args()
    acciones = {None: cmd_registrar, "ver": cmd_ver, "agregar": cmd_agregar, "grafica": cmd_grafica}
    return acciones[args.comando](args)


if __name__ == "__main__":
    sys.exit(main())
