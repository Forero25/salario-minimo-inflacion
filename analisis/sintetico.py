"""Control sintético: ¿se desvió la inflación de Colombia en 2026 de la de una combinación de países que la imitaba antes?

Inflación anual mensual del BIS. Periodo de ajuste: enero de 2023 a diciembre de 2025. Los pesos son no negativos y suman 1.
Inferencia con placebos: se repite el ejercicio tratando a cada país como si fuera el tratado.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .datos import leer, registros

NOMBRES = {"CO": "Colombia", "CL": "Chile", "PE": "Perú", "MX": "México", "BR": "Brasil", "ZA": "Sudáfrica", "IN": "India", "ID": "Indonesia",
           "PH": "Filipinas", "TH": "Tailandia", "MY": "Malasia", "TR": "Turquía", "PL": "Polonia", "HU": "Hungría", "CZ": "Chequia",
           "RO": "Rumania", "KR": "Corea del Sur", "IL": "Israel", "AU": "Australia", "NZ": "Nueva Zelanda", "CA": "Canadá", "NO": "Noruega",
           "SE": "Suecia", "GB": "Reino Unido", "US": "Estados Unidos", "JP": "Japón"}


def matriz(inicio: int = 202101) -> pd.DataFrame:
    b = leer("select pais, anio, mes, inflacion_anual from staging.stg_bis order by pais, anio, mes")
    b["t"] = b.anio * 100 + b.mes
    w = b.pivot(index="t", columns="pais", values="inflacion_anual")
    fin = int(w["CO"].dropna().index.max())
    return w.loc[inicio:fin].dropna(axis=1)


def ajustar(w: pd.DataFrame, tratado: str, pre=(202301, 202512)):
    donantes = [c for c in w.columns if c != tratado]
    pre_w, post_w = w.loc[pre[0]:pre[1]], w.loc[pre[1] + 1 - 12 + 100:]  # desde enero del año siguiente
    X, y = pre_w[donantes].to_numpy(), pre_w[tratado].to_numpy()
    n = len(donantes)
    r = minimize(lambda a: ((y - X @ a) ** 2).mean(), np.ones(n) / n, bounds=[(0, 1)] * n,
                 constraints={"type": "eq", "fun": lambda a: a.sum() - 1}, method="SLSQP", options={"maxiter": 500, "ftol": 1e-12})
    a = np.clip(r.x, 0, None); a = a / a.sum()
    sint = w[donantes].to_numpy() @ a
    brecha = w[tratado].to_numpy() - sint
    pre_m = (w.index >= pre[0]) & (w.index <= pre[1]); post_m = w.index > pre[1]
    return {"pesos": dict(zip(donantes, a)), "serie": pd.DataFrame({"t": w.index, "real": w[tratado].to_numpy(), "sintetico": sint, "brecha": brecha}),
            "rmspe_pre": float(np.sqrt((brecha[pre_m] ** 2).mean())), "rmspe_post": float(np.sqrt((brecha[post_m] ** 2).mean())),
            "brecha_media_post": float(brecha[post_m].mean())}


def correr() -> dict:
    w = matriz()
    co = ajustar(w, "CO")
    plac = []
    for c in w.columns:
        r = ajustar(w, c)
        plac.append({"pais": c, "nombre": NOMBRES.get(c, c), "razon": r["rmspe_post"] / r["rmspe_pre"], "brecha_media_post": r["brecha_media_post"], "rmspe_pre": r["rmspe_pre"]})
    plac = pd.DataFrame(plac).sort_values("razon", ascending=False).reset_index(drop=True)
    puesto = int(plac.index[plac.pais == "CO"][0]) + 1
    otro = ajustar(w, "CO", pre=(202101, 202512))
    pesos = sorted(((NOMBRES.get(k, k), v) for k, v in co["pesos"].items() if v >= 0.01), key=lambda x: -x[1])
    s = co["serie"]; s["anio"] = s.t // 100; s["mes"] = s.t % 100
    return {"pesos": [{"pais": k, "peso": v} for k, v in pesos], "serie": registros(s[s.t >= 202301].drop(columns="t")),
            "rmspe_pre": co["rmspe_pre"], "rmspe_post": co["rmspe_post"], "brecha_media_post": co["brecha_media_post"],
            "brecha_ultimo": float(s.brecha.iloc[-1]), "ultimo": {"anio": int(s.anio.iloc[-1]), "mes": int(s.mes.iloc[-1])},
            "puesto": puesto, "paises": int(len(plac)), "p_placebo": puesto / len(plac),
            "placebos": registros(plac), "ajuste_desde_2021": {"brecha_media_post": otro["brecha_media_post"], "rmspe_pre": otro["rmspe_pre"]}}
