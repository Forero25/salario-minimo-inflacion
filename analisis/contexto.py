"""Contexto: aumentos del salario mínimo frente a la inflación del año anterior, e inflación mensual reciente."""
from __future__ import annotations

from .datos import leer, registros


def inflacion_diciembre() -> dict:
    t = leer("select anio, var_anual from staging.stg_ipc_total where mes = 12 and var_anual is not null order by anio")
    return dict(zip(t.anio.astype(int), t.var_anual))


def aumentos() -> list[dict]:
    infl = inflacion_diciembre()
    s = leer("select anio, smmlv, aumento from staging.stg_salario_minimo where anio >= 2005 order by anio")
    s["inflacion_previa"] = s.anio.map(lambda a: infl.get(a - 1))
    s["real"] = s.aumento - s.inflacion_previa
    return registros(s)


def correr() -> dict:
    a = aumentos()
    t = leer("select anio, mes, var_anual, var_mensual from staging.stg_ipc_total where anio >= 2019 order by anio, mes")
    v = leer("select * from marts.validacion_laspeyres order by anio, mes")
    ult = t.dropna().iloc[-1]
    return {"aumentos": a, "inflacion_mensual": registros(t), "ultimo": {"anio": int(ult.anio), "mes": int(ult.mes), "var_anual": ult.var_anual},
            "validacion": {"meses": int(len(v)), "max_dif_abs": float(v.diferencia.abs().max()), "subclases": 188}}
