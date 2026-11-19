"""Diseño por exposición entre productos: subclases del IPC según la proporción de trabajadores en el mínimo en el sector que las produce."""
from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf

from .contexto import inflacion_diciembre
from .datos import leer, registros

SERVICIOS = {"05620100": "Servicio doméstico", "11110100": "Comidas en establecimientos de servicio a la mesa", "12110100": "Peluquería y salones de belleza",
             "04440100": "Administración de la vivienda", "10110400": "Educación preescolar y básica primaria", "07371000": "Transporte urbano"}


def panel() -> pd.DataFrame:
    p = leer("select * from marts.panel_subclases where coalesce(marca, '') <> 'imputado' order by codigo, anio")
    infl = inflacion_diciembre()
    p["real"] = p.aumento_sm - p.anio.map(lambda a: infl.get(a - 1))
    p["nucleo"] = p.marca.isna() & ~p.codigo.str[:2].isin(["01", "02"])
    return p


def estimar(d: pd.DataFrame, y="var_t1", e="en_minimo", pesos=True) -> dict:
    d = d.dropna(subset=[y]).copy()
    d["x"] = d.real * d[e]
    f = smf.wls(f"{y} ~ x + C(codigo) + C(anio)", d, weights=d.ponderacion if pesos else None) if pesos else smf.ols(f"{y} ~ x + C(codigo) + C(anio)", d)
    m = f.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["codigo"])[0]})
    ic = m.conf_int().loc["x"]
    return {"beta": m.params["x"], "ee": m.bse["x"], "p": m.pvalues["x"], "ic_bajo": ic[0], "ic_alto": ic[1], "subclases": int(d.codigo.nunique()), "n": int(m.nobs)}


def correr() -> dict:
    p = panel()
    t1 = p.pivot_table(index=["codigo", "subclase"], columns="anio", values="var_t1").reset_index()
    t1["previo"] = t1[[2023, 2024, 2025]].mean(axis=1)
    s = t1[t1.codigo.isin(SERVICIOS)].copy()
    s["nombre"] = s.codigo.map(SERVICIOS)
    s = s.rename(columns={2025: "t1_2025", 2026: "t1_2026"})[["codigo", "nombre", "t1_2025", "t1_2026", "previo"]]
    ind = t1[t1.codigo.isin(p[p.marca == "indexado"].codigo)].rename(columns={2025: "t1_2025", 2026: "t1_2026"})[["codigo", "subclase", "t1_2025", "t1_2026", "previo"]]
    return {
        "todas": estimar(p), "sin_pesos": estimar(p, pesos=False), "nucleo": estimar(p[p.nucleo]),
        "hasta_15": estimar(p, e="hasta_15"), "placebo_t3": estimar(p, "var_t3"),
        "servicios": registros(s), "indexados": registros(ind),
    }
