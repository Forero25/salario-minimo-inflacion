import json
from pathlib import Path

import numpy as np
import pandas as pd

from analisis import ciudades

RES = Path(__file__).resolve().parents[1] / "resultados"


def test_el_diseno_recupera_un_efecto_conocido_y_no_inventa_uno():
    """Con datos simulados con β = 0,2 el estimador lo recupera; con β = 0 no encuentra nada."""
    rng = np.random.default_rng(0)
    ciu = [f"c{i}" for i in range(24)]
    expo = dict(zip(ciu, rng.uniform(0.1, 0.45, 24)))
    filas = []
    for b in [0.2, 0.0]:
        for a, real in zip(range(2017, 2027), [1, 0.5, 2.8, 2.2, 1.9, 4.4, 2.9, 2.8, 4.3, 17.9]):
            choque_anio = rng.normal(0, 1)
            for c in ciu:
                filas.append({"b": b, "ciudad": c, "anio": a, "real": real, "en_minimo": expo[c],
                              "var_t1": 1 + choque_anio + 0.3 * expo[c] + b * real * expo[c] + rng.normal(0, 0.25)})
    d = pd.DataFrame(filas)
    con = ciudades.estimar(d[d.b == 0.2])
    sin = ciudades.estimar(d[d.b == 0.0])
    assert con["ic_bajo"] < 0.2 < con["ic_alto"] and con["p"] < 0.05
    assert sin["p"] > 0.05


def test_validacion_laspeyres():
    c = json.loads((RES / "contexto.json").read_text())
    assert c["validacion"]["max_dif_abs"] < 0.1 and c["validacion"]["subclases"] == 188


def test_resultados_coherentes():
    c = json.loads((RES / "ciudades.json").read_text())
    assert c["principal"]["ciudades"] == 24
    assert c["placebo_t3"]["p"] > 0.05  # el placebo no debe mostrar efecto
    s = json.loads((RES / "sintetico.json").read_text())
    assert abs(sum(p["peso"] for p in s["pesos"]) - 1) < 0.05


def test_extraccion_del_parrafo_del_mes():
    from analisis.texto import extraer
    t = ("En enero de 2026 en comparación con diciembre de 2025, la variación de las subclases que más aportaron al índice total fueron: "
         "comidas en establecimientos de servicio a la mesa y autoservicio (3,36%), transporte urbano (incluye tren y metro) (5,11%) "
         "y servicio doméstico (5,16%). Las subclases con mayores aportes negativos fueron: electricidad (-0,91%). "
         "En lo corrido del año, en comparación con diciembre de 2024, la variación de las subclases que más aportaron al índice total fueron: arriendo (9,99%). Fin.")
    r = extraer(t, 2026, 1)
    assert [n for n, _ in r] == ["comidas en establecimientos de servicio a la mesa y autoservicio", "transporte urbano (incluye tren y metro)", "servicio doméstico"]
    assert [v for _, v in r] == [3.36, 5.11, 5.16]
