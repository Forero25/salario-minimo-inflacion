from __future__ import annotations

import json
import math
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("SM_DB", RAIZ / "data" / "salario.duckdb"))
RES = RAIZ / "resultados"

def leer(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DB), read_only=True) as c:
        return c.sql(sql).df()


def limpio(o):
    if isinstance(o, dict):
        return {str(k): limpio(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpio(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else round(float(o), 4)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return o


def registros(df: pd.DataFrame) -> list[dict]:
    return limpio(df.to_dict(orient="records"))


def guardar(nombre: str, obj) -> None:
    RES.mkdir(exist_ok=True)
    with open(RES / f"{nombre}.json", "w", encoding="utf-8") as f:
        json.dump(limpio(obj), f, ensure_ascii=False, indent=1, allow_nan=False)
