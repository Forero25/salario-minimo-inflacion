"""Análisis de texto de los boletines técnicos mensuales del IPC (DANE, 2019 en adelante).

1. Extrae del PDF el párrafo donde el DANE nombra las subclases que más aportaron a la inflación del mes, con su variación.
2. Asocia cada nombre con su código de subclase (TF-IDF de n-gramas de caracteres y similitud coseno).
3. Valida la extracción: la variación escrita en el texto debe coincidir con la calculada con los índices.
4. Mide qué parte del "relato" del mes se lo llevan los servicios intensivos en trabajo, antes y después del aumento de 2026.
"""
from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .datos import RAIZ, leer, registros

DIR = Path(__import__("os").environ.get("SM_BOLETINES", RAIZ / "data" / "raw" / "boletines"))
# Clases COICOP de servicios cuyo costo principal es el trabajo (no regulados, no arriendos, no financieros ni comunicaciones)
TRABAJO = {"0314", "0444", "0562", "0621", "0622", "0623", "0631", "0723", "0935", "0941", "1011", "1021", "1041", "1051",
           "1111", "1112", "1121", "1211"}
POS = re.compile(r"subclases\s+que\s+m[aá]s\s+aportaron\s+a[l]?\s+(?:la\s+variaci[oó]n|[ií]ndice\s+total|IPC)[^:]*:\s*(.*?)\.\s+(?=[A-ZÁÉÍÓÚ])", re.S)
ITEM = re.compile(r"\s*(?:y\s+)?(.+?)\s*\((-?\d+[,.]\d+)\s*%\)\s*,?")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()


def texto(pdf: Path) -> str:
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def extraer(t: str, anio: int, mes: int) -> list[tuple[str, float]]:
    """El boletín trae el párrafo tres veces (mes, año corrido y doce meses). Se toma el que compara con el mes anterior."""
    pa, pm = (anio - 1, 12) if mes == 1 else (anio, mes - 1)
    previo = re.compile(rf"comparaci[oó]n\s+con\s+{MESES[pm - 1]}\s+(?:de\s+)?{pa}", re.I)
    candidatos = [m for m in POS.finditer(t) if previo.search(t[max(0, m.start() - 300):m.start()])]
    if not candidatos:
        return []
    m = candidatos[0]
    bloque = re.sub(r"\s+", " ", m.group(1))
    return [(n.strip(" ,;"), float(v.replace(",", "."))) for n, v in ITEM.findall(bloque)]


def corpus() -> pd.DataFrame:
    filas = []
    for pdf in sorted(DIR.glob("*.pdf")):
        anio, mes = map(int, pdf.stem.split("-"))
        t = texto(pdf)
        items = extraer(t, anio, mes)
        for rk, (nombre, v) in enumerate(items, 1):
            filas.append({"anio": anio, "mes": mes, "puesto": rk, "nombre_texto": nombre, "var_texto": v})
        filas.append({"anio": anio, "mes": mes, "puesto": 0, "nombre_texto": None, "var_texto": None,
                      "menciones_salario_minimo": len(re.findall(r"salario\s+m[ií]nimo", t, re.I)), "palabras": len(t.split())})
    return pd.DataFrame(filas)


def asociar(c: pd.DataFrame) -> pd.DataFrame:
    sub = leer("select distinct codigo, subclase, clase from staging.stg_subclases order by codigo")
    sub["n"] = sub.subclase.map(norm)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(sub.n.tolist() + c.nombre_texto.dropna().map(norm).tolist())
    x = c[c.puesto > 0].copy()
    tx = x.nombre_texto.map(norm).tolist()
    # el DANE abrevia los nombres largos en el texto: se compara contra el nombre completo y contra su comienzo
    S_full = cosine_similarity(vec.transform(tx), vec.transform(sub.n))
    S_pref = np.zeros_like(S_full)
    for i, t in enumerate(tx):
        S_pref[i] = cosine_similarity(vec.transform([t]), vec.transform([n[: len(t) + 3] for n in sub.n]))[0]
    S = np.maximum(S_full, S_pref)
    x["codigo"] = sub.codigo.to_numpy()[S.argmax(1)]
    x["similitud"] = S.max(1)
    x = x.merge(sub[["codigo", "subclase", "clase"]], on="codigo")
    v = leer("select codigo, anio, mes, var_mensual from staging.stg_subclases")
    x = x.merge(v, on=["codigo", "anio", "mes"], how="left")
    x["coincide"] = (x.var_texto - x.var_mensual).abs() <= 0.015
    x["trabajo"] = x.clase.isin(TRABAJO)
    return x.sort_values(["anio", "mes", "puesto"])


def correr() -> dict:
    c = corpus()
    meta = c[c.puesto == 0]
    x = asociar(c)
    por_mes = x.groupby(["anio", "mes"]).agg(nombradas=("codigo", "size"), trabajo=("trabajo", "sum"),
                                            primeras3_trabajo=("trabajo", lambda s: s.head(3).sum())).reset_index()
    por_mes["pct_trabajo"] = por_mes.trabajo / por_mes.nombradas
    ene_abr = por_mes[por_mes.mes <= 4]
    comp = ene_abr.groupby(ene_abr.anio == 2026).pct_trabajo.mean()
    resto = por_mes[por_mes.mes > 4]
    # qué subclases nombra el DANE en enero de cada año
    eneros = x[x.mes == 1].groupby("anio").apply(lambda d: [n for n in d.subclase.head(10)], include_groups=False).to_dict()
    frecuentes = x.groupby(["codigo", "subclase", "trabajo"]).size().rename("meses").reset_index().nlargest(15, "meses")
    return {
        "boletines": int(meta.shape[0]), "con_parrafo": int(x.groupby(["anio", "mes"]).ngroups),
        "menciones_extraidas": int(len(x)),
        "validacion": {"coinciden": int(x.coincide.sum()), "con_dato": int(x.var_mensual.notna().sum()),
                       "tasa": float(x.coincide.sum() / x.var_mensual.notna().sum()), "similitud_min": float(x.similitud.min()),
                       "similitud_mediana": float(x.similitud.median())},
        "menciones_salario_minimo": int(meta.menciones_salario_minimo.sum()),
        "por_mes": registros(por_mes),
        "ene_abr": {"2026": float(comp.get(True, np.nan)), "2019_2025": float(comp.get(False, np.nan))},
        "ene_abr_por_anio": registros(ene_abr.groupby("anio").pct_trabajo.mean().reset_index()),
        "resto_del_anio": registros(resto.groupby("anio").pct_trabajo.mean().reset_index()),
        "eneros": {str(k): v for k, v in eneros.items()},
        "frecuentes": registros(frecuentes),
        "no_coinciden": registros(x[~x.coincide & x.var_mensual.notna()][["anio", "mes", "nombre_texto", "subclase", "var_texto", "var_mensual", "similitud"]].head(20)),
    }
