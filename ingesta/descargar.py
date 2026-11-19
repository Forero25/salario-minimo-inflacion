"""Descarga las fuentes públicas del proyecto. Corre en GitHub Actions (desde el entorno de desarrollo no hay salida a esos sitios).

- DANE: anexos del IPC (índices por subclase con ponderaciones, serie empalmada total, variaciones por ciudad).
- BIS: índices de precios al consumidor mensuales de varios países (para el control sintético).
- Wikipedia (es): historia del salario mínimo en Colombia (para la serie de aumentos; se coteja con los decretos).
Los archivos van a data/raw/ y el flujo los publica en el release "crudos".
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (portafolio de datos públicos; github.com/Forero25/salario-minimo-inflacion)"}
DANE = "https://www.dane.gov.co/files"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
PAISES_BIS = ["CO", "CL", "PE", "MX", "BR", "UY", "PY", "CR", "DO", "GT", "HN", "ZA", "IN", "ID", "PH", "TH", "MY", "TR", "PL", "HU", "CZ", "RO", "KR", "IL", "AU", "NZ", "CA", "NO", "SE", "GB", "US", "JP"]


def bajar(url: str, intentos: int = 3) -> bytes | None:
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                b = r.read()
                if r.status == 200 and not b[:15].lower().startswith((b"<!doctype", b"<html")):
                    return b
                return None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(3 * (i + 1))
    return None


def subclases(anio_actual: int, mes_actual: int) -> None:
    """Un anexo por año: el de diciembre (o el último mes publicado) trae los índices de los 12 meses de ese año."""
    for anio in range(2019, anio_actual + 1):
        mes = MESES[mes_actual - 1] if anio == anio_actual else "dic"
        yy = str(anio)[2:]
        candidatos = [
            f"{DANE}/operaciones/IPC/{mes}{anio}/anex-IPC-subclases-ingresos-total-{mes}{anio}.xlsx",
            f"{DANE}/operaciones/IPC/{mes}{yy}/subclases-ingresos-total-{mes}{yy}.xlsx",
            f"{DANE}/investigaciones/ipc/{mes}{yy}/subclases-ingresos-total-{mes}{yy}.xlsx",
            f"{DANE}/investigaciones/ipc/{mes}{yy}/anex-IPC-subclases-ingresos-total-{mes}{yy}.xlsx",
            f"{DANE}/investigaciones/ipc/{mes}{anio}/anex-IPC-subclases-ingresos-total-{mes}{anio}.xlsx",
            f"{DANE}/investigaciones/ipc/{mes}{yy}/subclases-total-{mes}{yy}.xlsx",
            f"{DANE}/investigaciones/ipc/{mes}{yy}/IPC_Subclases_{mes}{yy}.xlsx",
        ]
        for u in candidatos:
            b = bajar(u)
            if b:
                (RAW / f"subclases_{anio}.xlsx").write_bytes(b)
                print("ok subclases", anio, u)
                break
        else:
            print("FALTA subclases", anio)


def anexos_actuales(anio: int, mes: int) -> None:
    m = f"{MESES[mes - 1]}{anio}"
    for nombre, archivo in [("indices", f"anex-IPC-Indices-{m}.xlsx"), ("ciudades_mensual", f"anex-IPC-CiudadesMensuales-{m}.xlsx"),
                            ("divisiones", f"anex-IPC-divisiones-ingresos-total-{m}.xlsx")]:
        b = bajar(f"{DANE}/operaciones/IPC/{m}/{archivo}")
        if not b:
            raise SystemExit(f"no se pudo bajar {archivo}")
        (RAW / f"{nombre}.xlsx").write_bytes(b)
        print("ok", nombre)


def ultimo_publicado() -> tuple[int, int]:
    """El mes más reciente con anexos publicados (el DANE publica el IPC de un mes en los primeros días del siguiente)."""
    t = time.gmtime()
    a, m = t.tm_year, t.tm_mon
    for _ in range(4):
        m -= 1
        if m == 0:
            a, m = a - 1, 12
        if bajar(f"{DANE}/operaciones/IPC/{MESES[m - 1]}{a}/anex-IPC-Indices-{MESES[m - 1]}{a}.xlsx"):
            return a, m
    raise SystemExit("no encontré anexos recientes del IPC")


def bis() -> None:
    filas = []
    for c in PAISES_BIS:
        b = bajar(f"https://stats.bis.org/api/v2/data/dataflow/BIS/WS_LONG_CPI/1.0/M.{c}.771?format=csv")
        if b:
            filas.append(b.decode())
            print("ok BIS", c)
        else:
            print("falta BIS", c)
    cab = filas[0].splitlines()[0]
    with open(RAW / "bis_ipc.csv", "w") as f:
        f.write(cab + "\n" + "\n".join("\n".join(x.splitlines()[1:]) for x in filas) + "\n")


def wikipedia() -> None:
    q = urllib.parse.urlencode({"action": "parse", "page": "Salario mínimo en Colombia", "prop": "wikitext", "format": "json", "formatversion": 2, "redirects": 1})
    b = bajar(f"https://es.wikipedia.org/w/api.php?{q}")
    (RAW / "wiki_salario_minimo.json").write_bytes(b)
    print("ok wikipedia", len(json.loads(b)["parse"]["wikitext"]))


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    a, m = ultimo_publicado()
    print("último mes publicado:", a, m)
    (RAW / "ultimo_mes.txt").write_text(f"{a}-{m:02d}\n")
    anexos_actuales(a, m)
    subclases(a, m)
    bis()
    wikipedia()


if __name__ == "__main__":
    main()
    sys.exit(0)
