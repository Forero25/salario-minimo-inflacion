"""Convierte los anexos del DANE, la serie del BIS y la tabla de Wikipedia en tablas ordenadas (data/interim/*.csv)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RAW, INT = RAIZ / "data" / "raw", RAIZ / "data" / "interim"
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def subclases() -> pd.DataFrame:
    filas = []
    for f in sorted(RAW.glob("subclases_*.xlsx")):
        anio = int(f.stem.split("_")[1])
        d = pd.read_excel(f, header=None, dtype={0: str})
        cab = d.index[d.iloc[:, 3].astype(str).str.strip() == "Enero"][0]
        meses = [str(x).strip() for x in d.iloc[cab, 3:15]]
        d = d[d[0].astype(str).str.fullmatch(r"\d{8}")]
        for _, r in d.iterrows():
            for j, m in enumerate(meses):
                v = pd.to_numeric(r[3 + j], errors="coerce")
                if m in MESES and pd.notna(v):
                    filas.append({"codigo": r[0], "subclase": str(r[1]).strip(), "ponderacion": float(r[2]),
                                  "anio": anio, "mes": MESES.index(m) + 1, "indice": float(v)})
    s = pd.DataFrame(filas)
    # el nombre de una subclase cambia de mayúsculas entre años: se usa el del último año
    s["subclase"] = s.groupby("codigo")["subclase"].transform("last")
    return s


def ipc_total() -> pd.DataFrame:
    d = pd.read_excel(RAW / "indices.xlsx", header=None)
    cab = d.index[d[0].astype(str).str.strip() == "Mes"][0]
    anios = [int(float(x)) for x in d.iloc[cab, 1:] if pd.notna(x)]
    filas = []
    for i in range(cab + 1, cab + 13):
        mes = MESES.index(str(d.iloc[i, 0]).strip()) + 1
        for j, a in enumerate(anios):
            v = pd.to_numeric(d.iloc[i, 1 + j], errors="coerce")
            if pd.notna(v):
                filas.append({"anio": a, "mes": mes, "indice": float(v)})
    return pd.DataFrame(filas)


def ciudades() -> pd.DataFrame:
    d = pd.read_excel(RAW / "ciudades_mensual.xlsx", header=None)
    filas, anio = [], None
    for i in range(len(d)):
        c0 = str(d.iloc[i, 0])
        m = re.search(r"Variaciones mensuales (\d{4})", c0)
        if m:
            anio = int(m.group(1)); continue
        if anio and pd.notna(d.iloc[i, 0]) and c0.strip() not in ("Ciudad", "nan") and not c0.startswith(("Fuente", "Nota", "AÑO")):
            for j in range(12):
                v = pd.to_numeric(d.iloc[i, 1 + j], errors="coerce")
                if pd.notna(v):
                    filas.append({"ciudad": c0.strip(), "anio": anio, "mes": j + 1, "var_mensual": float(v)})
    return pd.DataFrame(filas)


def bis() -> pd.DataFrame:
    d = pd.read_csv(RAW / "bis_ipc.csv")
    d = d[d.UNIT_MEASURE.astype(str) == "771"]  # variación anual (%)
    d["anio"] = d.TIME_PERIOD.str[:4].astype(int); d["mes"] = d.TIME_PERIOD.str[5:7].astype(int)
    return d.rename(columns={"REF_AREA": "pais", "OBS_VALUE": "inflacion_anual"})[["pais", "anio", "mes", "inflacion_anual"]]


def salario_minimo() -> pd.DataFrame:
    """Tabla 'Salario mínimo en Colombia por año' de Wikipedia: se toma solo el salario mensual en pesos."""
    w = json.loads((RAW / "wiki_salario_minimo.json").read_text())["parse"]["wikitext"]
    t = w[w.find("== Tabla por año =="):]
    t = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\{\{esd\|?([^}]*)\}\}", lambda m: m.group(1).replace("|", ""), t)
    t = t.replace("&nbsp;", "").replace(" ", "")
    filas = []
    for bloque in re.split(r"\n\|-", t):
        m = re.match(r"\s*!\s*(\d{4})\s*\n(.*)", bloque, re.S)
        if not m:
            continue
        celdas = [c.strip() for c in re.split(r"\|\||\n\|", "\n" + m.group(2).rstrip())][1:]
        if len(celdas) < 3:
            continue
        mensual = re.sub(r"[^\d]", "", celdas[2].split(",")[0])
        if mensual:
            filas.append({"anio": int(m.group(1)), "smmlv": int(mensual)})
    s = pd.DataFrame(filas).drop_duplicates("anio").sort_values("anio")
    s["aumento"] = s.smmlv.pct_change() * 100
    s.loc[s.anio.diff() != 1, "aumento"] = None
    return s


def main() -> None:
    INT.mkdir(parents=True, exist_ok=True)
    for nombre, f in [("subclases", subclases), ("ipc_total", ipc_total), ("ciudades", ciudades), ("bis", bis), ("salario_minimo", salario_minimo)]:
        d = f(); d.to_csv(INT / f"{nombre}.csv", index=False); print(nombre, d.shape)


if __name__ == "__main__":
    main()
