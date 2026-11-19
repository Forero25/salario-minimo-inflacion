"""Corre todos los análisis y escribe resultados/*.json y publicado/*.csv."""
from __future__ import annotations

from . import ciudades, contexto, productos, sintetico
from .datos import RAIZ, guardar, leer


def publicar() -> None:
    pub = RAIZ / "publicado"; pub.mkdir(exist_ok=True)
    leer("select * from marts.panel_ciudades order by ciudad, anio").round(4).to_csv(pub / "panel_ciudades.csv", index=False)
    leer("""select codigo, subclase, clase, ponderacion, anio, tipo, marca, ciiu, var_ene, var_t1, var_t3, en_minimo, aumento_sm
            from marts.panel_subclases order by codigo, anio""").round(4).to_csv(pub / "panel_subclases.csv", index=False)
    leer("select ciudad, anio, mes, var_mensual from staging.stg_ciudades order by ciudad, anio, mes").to_csv(pub / "ciudades_mensual.csv", index=False)


def main() -> None:
    for nombre, mod in [("contexto", contexto), ("ciudades", ciudades), ("productos", productos), ("sintetico", sintetico)]:
        guardar(nombre, mod.correr()); print(nombre)
    publicar(); print("publicado")


if __name__ == "__main__":
    main()
