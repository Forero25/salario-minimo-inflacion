# Salario mínimo e inflación en Colombia

El salario mínimo de 2026 subió 23 %, casi 18 puntos por encima de la inflación de 2025: el aumento real más grande de la serie.
¿Cuánto de eso pasó a los precios? Este repositorio responde con datos públicos del DANE, la GEIH 2025, el BIS y tres diseños distintos.

- **Artículo:** [nicolasforero.pages.dev/escritos/salario-minimo-inflacion](https://nicolasforero.pages.dev/escritos/salario-minimo-inflacion/)
- **App interactiva** (Shiny for Python): `app.py`, publicada en Posit Connect Cloud.
- **Método detallado:** [METODO.md](METODO.md)

## Lo que encontré

Las cifras salen de `resultados/*.json`, que el pipeline recalcula cada mes cuando el DANE publica el IPC.

- **Ciudades:** las ciudades con más asalariados en el mínimo tuvieron más inflación de enero a marzo en los años de aumento real grande. En 2026 eso se traduce en cerca de 0,9 puntos más entre la ciudad más expuesta (Armenia) y la menos expuesta (Florencia). El placebo (julio a septiembre) no muestra nada. Es evidencia moderada: descansa casi toda en 2026 y la inferencia por permutación da p ≈ 0,05.
- **Productos:** el mismo diseño entre las 188 subclases del IPC, según la exposición del sector que las produce, no encuentra efecto. Los servicios intensivos en trabajo (servicio doméstico, restaurantes, peluquerías, administración de edificios) sí subieron más en 2026 que en años anteriores.
- **País:** la inflación de Colombia quedó alrededor de 1 punto por encima de su control sintético en 2026, pero esa desviación no es rara entre los placebos (puesto 7 de 23).

## Arquitectura

```
DANE (anexos del IPC), BIS, Wikipedia ──> ingesta/descargar.py (GitHub Actions) ──> release "crudos"
GEIH 2025 (microdatos, en el computador del autor) ──> geih/exposicion.py ──> entradas/exposicion_*.csv (solo agregados)
                                   │
          ingesta/preparar.py ──> dbt + DuckDB: staging.* y marts.* (paneles, validación Laspeyres) + 18 pruebas
                                   │
          analisis/ (contexto, ciudades, productos, sintetico) ──> resultados/*.json, publicado/*.csv ──> app.py
```

Todo corre en Docker (`Dockerfile`, `correr.sh`) en GitHub Actions el 12 de cada mes.

## Lo que no hace

- No mide el efecto del mínimo sobre el nivel general de precios: los efectos de año absorben todo lo que le pasa al país entero. Mide si los precios subieron **más** donde el mínimo pesa más.
- La identificación descansa casi toda en 2026; los años anteriores tuvieron aumentos reales pequeños y parecidos.
- La exposición es por ciudad y por sector (GEIH 2025), no por empresa.
- No incluye NLP de las minutas del Banco de la República: su sitio bloquea descargas automáticas con un captcha.
- El control sintético compara inflación agregada con 22 países; con tan pocos, la inferencia es gruesa.

## Datos y licencias

- DANE: IPC (anexos por subclase y por ciudad) y GEIH 2025. Información pública; se cita la fuente.
- [BIS](https://data.bis.org) (WS_LONG_CPI): precios al consumidor de 26 países.
- Salario mínimo por año: [Wikipedia](https://es.wikipedia.org/wiki/Salario_m%C3%ADnimo_en_Colombia) (CC BY-SA 4.0); el aumento se calcula con los niveles.

Código bajo licencia MIT. José Nicolás Forero Urrego · [nicolasforero.pages.dev](https://nicolasforero.pages.dev)
