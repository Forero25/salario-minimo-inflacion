"""Exposición al salario mínimo por sector (CIIU rev. 4, 2 dígitos) y por ciudad, con la GEIH 2025 (DANE).

Corre en el computador donde están los microdatos; solo salen agregados (ninguna fila de persona).
Asalariados (P6430 = 1, 2 o 3) con ingreso mensual de su empleo principal (P6500). SMMLV 2025 = 1.423.500.
"en el mínimo": entre 0,95 y 1,05 SMMLV; "hasta 1,5": de 0,95 a 1,5 SMMLV; "bajo el mínimo": menos de 0,95.
Factor de expansión FEX_C18 / 12 (doce meses apilados).
"""
import glob, os, sys
import pandas as pd

SMMLV = 1_423_500
RAIZ = sys.argv[1]
COLS = ["MES", "AREA", "CLASE", "FEX_C18", "P6430", "P6500", "P6800", "P6920", "RAMA2D_R4"]
meses = []
for c in sorted(glob.glob(os.path.join(RAIZ, "* 2025"))):
    a = [f for f in os.listdir(os.path.join(c, "CSV")) if f.startswith("Ocupados")][0]
    meses.append(pd.read_csv(os.path.join(c, "CSV", a), sep=";", usecols=lambda x: x in COLS, dtype=str, encoding="latin1", low_memory=False))
d = pd.concat(meses, ignore_index=True)
assert d.MES.nunique() == 12, d.MES.unique()
for c in ["AREA", "CLASE", "FEX_C18", "P6430", "P6500", "P6800", "P6920"]:
    d[c] = pd.to_numeric(d[c].str.replace(",", "."), errors="coerce")
d["w"] = d.FEX_C18 / 12
d["ocupados"] = 1
a = d[d.P6430.isin([1, 2, 3]) & (d.P6500 > 0)].copy()
r = a.P6500 / SMMLV
a["en_minimo"] = r.between(0.95, 1.05)
a["hasta_15"] = r.between(0.95, 1.5)
a["bajo_minimo"] = r < 0.95
a["cotiza"] = a.P6920 == 1


def agregar(df, por):
    g = df.groupby(por)
    out = pd.DataFrame({
        "asalariados": g.w.sum(),
        "n_muestra": g.size(),
        "en_minimo": g.apply(lambda x: (x.w * x.en_minimo).sum() / x.w.sum(), include_groups=False),
        "hasta_15": g.apply(lambda x: (x.w * x.hasta_15).sum() / x.w.sum(), include_groups=False),
        "bajo_minimo": g.apply(lambda x: (x.w * x.bajo_minimo).sum() / x.w.sum(), include_groups=False),
        "en_minimo_cotizantes": g.apply(lambda x: (x.w * (x.en_minimo & x.cotiza)).sum() / x.w.sum(), include_groups=False),
    })
    return out.reset_index()


os.makedirs("salida", exist_ok=True)
sec = agregar(a, "RAMA2D_R4")
sec.to_csv("salida/exposicion_sector.csv", index=False)
ciu = agregar(a[a.AREA.notna()], "AREA")
ciu["AREA"] = ciu["AREA"].astype(int)
ciu.to_csv("salida/exposicion_ciudad.csv", index=False)
tot = agregar(a.assign(t="total"), "t")
tot.to_csv("salida/exposicion_total.csv", index=False)
print(tot.to_string()); print(sec.sort_values("en_minimo", ascending=False).head(12).to_string()); print(ciu.to_string())
