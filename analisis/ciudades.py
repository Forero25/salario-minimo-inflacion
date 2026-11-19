"""Diseño por exposición entre ciudades: ¿suben más los precios a comienzo de año donde más trabajadores ganan el mínimo?

y(c, t) = ciudad + año + β · (aumento real del mínimo en t) × (exposición de c) + error, con errores agrupados por ciudad.
Exposición: proporción de asalariados que ganan entre 0,95 y 1,05 salarios mínimos (GEIH 2025).
Aumento real: aumento del mínimo menos la inflación del año anterior (la parte que no es indexación).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from .contexto import inflacion_diciembre
from .datos import leer, registros

EXPOS = {"en_minimo": "Entre 0,95 y 1,05 mínimos", "hasta_15": "Entre 0,95 y 1,5 mínimos", "en_minimo_cotizantes": "En el mínimo y cotizando a pensión"}


def panel() -> pd.DataFrame:
    p = leer("select * from marts.panel_ciudades order by ciudad, anio")
    infl = inflacion_diciembre()
    p["inflacion_previa"] = p.anio.map(lambda a: infl.get(a - 1))
    p["real"] = p.aumento_sm - p.inflacion_previa
    return p


def estimar(p: pd.DataFrame, y: str = "var_t1", e: str = "en_minimo", choque: str = "real") -> dict:
    d = p.dropna(subset=[y]).copy()
    d["x"] = d[choque] * d[e]
    m = smf.ols(f"{y} ~ x + C(ciudad) + C(anio)", d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["ciudad"])[0]})
    ic = m.conf_int().loc["x"]
    return {"beta": m.params["x"], "ee": m.bse["x"], "p": m.pvalues["x"], "ic_bajo": ic[0], "ic_alto": ic[1], "n": int(m.nobs),
            "ciudades": int(d.ciudad.nunique()), "anios": [int(d.anio.min()), int(d.anio.max())]}


def inferencia_aleatoria(p: pd.DataFrame, reps: int = 2000, semilla: int = 3) -> dict:
    """Se reparten las exposiciones al azar entre ciudades: ¿qué tan raro es el β observado si la exposición no importara?"""
    rng = np.random.default_rng(semilla)
    d = p.dropna(subset=["var_t1"]).copy()
    # con efectos fijos de ciudad y año, β sale de la regresión de los residuos (Frisch-Waugh)
    def residuo(v):
        return v - v.groupby(d.ciudad).transform("mean") - v.groupby(d.anio).transform("mean") + v.mean()
    yr = residuo(d.var_t1)
    obs = estimar(d)["beta"]
    expo = d.groupby("ciudad").en_minimo.first()
    ciudades = expo.index.to_numpy()
    betas = []
    for _ in range(reps):
        perm = dict(zip(ciudades, rng.permutation(expo.to_numpy())))
        xr = residuo(d.real * d.ciudad.map(perm))
        betas.append((xr * yr).sum() / (xr * xr).sum())
    betas = np.array(betas)
    return {"beta": obs, "p_dos_colas": float((np.abs(betas) >= abs(obs)).mean()), "reps": reps}


def sin_cada_ciudad(p: pd.DataFrame) -> dict:
    b = [estimar(p[p.ciudad != c])["beta"] for c in sorted(p.ciudad.unique())]
    return {"min": min(b), "max": max(b)}


def mes_a_mes(evento: int) -> list[dict]:
    """Para cada mes del año evento: pendiente entre (inflación de la ciudad ese mes − su promedio del mismo mes en los
    tres años anteriores) y la exposición."""
    c = leer("""select c.ciudad, c.anio, c.mes, c.var_mensual, e.en_minimo from staging.stg_ciudades c
                join staging.stg_exposicion_ciudad e using (ciudad) order by ciudad, anio, mes""")
    base = c[c.anio.between(evento - 3, evento - 1)].groupby(["ciudad", "mes"]).var_mensual.mean().rename("base")
    x = c[c.anio == evento].join(base, on=["ciudad", "mes"])
    x["d"] = x.var_mensual - x.base
    out = []
    for mes, g in x.groupby("mes"):
        m = sm.OLS(g.d, sm.add_constant(g.en_minimo)).fit(cov_type="HC1")
        ic = m.conf_int().loc["en_minimo"]
        out.append({"mes": int(mes), "pendiente": m.params["en_minimo"], "ic_bajo": ic[0], "ic_alto": ic[1], "p": m.pvalues["en_minimo"]})
    return out


def correr() -> dict:
    p = panel()
    princ = estimar(p)
    expo = p.groupby("ciudad")[["en_minimo", "hasta_15", "n_muestra"]].first().sort_values("en_minimo")
    real26 = float(p.loc[p.anio == 2026, "real"].iloc[0])
    alta, baja = expo.en_minimo.max(), expo.en_minimo.min()
    c26 = p[p.anio == 2026][["ciudad", "var_t1", "en_minimo"]].copy()
    prev = p[p.anio.between(2023, 2025)].groupby("ciudad").var_t1.mean().rename("t1_previo")
    c26 = c26.join(prev, on="ciudad")
    c26["exceso"] = c26.var_t1 - c26.t1_previo
    c26["predicho_extra"] = princ["beta"] * real26 * (c26.en_minimo - baja)
    return {
        "principal": princ,
        "placebo_t3": estimar(p, "var_t3"),
        "solo_enero": estimar(p, "var_ene"),
        "nominal": estimar(p, choque="aumento_sm"),
        "otras_exposiciones": {k: estimar(p, e=k) for k in EXPOS},
        "sin_2026": estimar(p[p.anio < 2026]),
        "inferencia_aleatoria": inferencia_aleatoria(p),
        "sin_cada_ciudad": sin_cada_ciudad(p),
        "mes_a_mes_2026": mes_a_mes(2026),
        "mes_a_mes_2025": mes_a_mes(2025),
        "exposicion": registros(expo.reset_index()),
        "real_2026": real26,
        "brecha_2026": {"alta": alta, "baja": baja, "ciudad_alta": expo.en_minimo.idxmax(), "ciudad_baja": expo.en_minimo.idxmin(),
                        "extra_t1": princ["beta"] * real26 * (alta - baja)},
        "ciudades_2026": registros(c26.sort_values("en_minimo")),
    }
