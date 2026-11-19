"""Descarga los boletines técnicos mensuales del IPC del DANE (2019 en adelante) para el análisis de texto.

El DANE cambió varias veces la ruta de los archivos; se prueban las variantes conocidas y las que aparecen enlazadas
en las páginas del IPC. Los PDF van a data/raw/boletines/ y el flujo los publica en el release "boletines".
"""
from __future__ import annotations

import re
import time
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "boletines"
UA = {"User-Agent": "Mozilla/5.0 (portafolio de datos públicos; github.com/Forero25/salario-minimo-inflacion)"}
D = "https://www.dane.gov.co"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
PAGINAS = ["/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc",
           "/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc/ipc-historico"]


def bajar(url: str) -> bytes | None:
    for i in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                b = r.read()
                return b if b[:4] == b"%PDF" else None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            time.sleep(3)
    return None


def enlazados() -> list[str]:
    out = []
    for p in PAGINAS:
        try:
            h = urllib.request.urlopen(urllib.request.Request(D + p, headers=UA), timeout=90).read().decode("utf-8", "ignore")
            out += re.findall(r'href="([^"]*bol[^"]*ipc[^"]*\.pdf)"', h, flags=re.I)
        except Exception as e:
            print("no pude leer", p, e)
    return sorted(set(out))


def candidatos(anio: int, mes: int) -> list[str]:
    m, yy = MESES[mes - 1], str(anio)[2:]
    return [f"/files/operaciones/IPC/{m}{anio}/bol-IPC-{m}{anio}.pdf", f"/files/operaciones/IPC/{m}{yy}/bol-IPC-{m}{yy}.pdf",
            f"/files/operaciones/IPC/{m}{yy}/bol_ipc_{m}{yy}.pdf", f"/files/investigaciones/ipc/{m}{yy}/bol-IPC-{m}{yy}.pdf",
            f"/files/investigaciones/ipc/{m}{yy}/bol_ipc_{m}{yy}.pdf", f"/files/investigaciones/boletines/ipc/bol_ipc_{m}{yy}.pdf",
            f"/files/investigaciones/boletines/ipc/bol-IPC-{m}{yy}.pdf", f"/files/investigaciones/boletines/ipc/bol_ipc_{m}{anio}.pdf"]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    links = enlazados()
    print("enlazados:", len(links))
    t = time.gmtime()
    faltan = []
    for anio in range(2019, t.tm_year + 1):
        for mes in range(1, 13):
            if (anio, mes) >= (t.tm_year, t.tm_mon):
                break
            destino = RAW / f"{anio}-{mes:02d}.pdf"
            if destino.exists():
                continue
            m, yy = MESES[mes - 1], str(anio)[2:]
            extra = [l for l in links if re.search(rf"{m}_?-?{yy}\b|{m}{anio}", l, re.I)]
            for ruta in candidatos(anio, mes) + extra:
                b = bajar(ruta if ruta.startswith("http") else D + ruta)
                if b:
                    destino.write_bytes(b); print("ok", anio, mes, ruta); break
            else:
                faltan.append(f"{anio}-{mes:02d}")
    print("faltan:", faltan)


if __name__ == "__main__":
    main()
