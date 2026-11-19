#!/usr/bin/env bash
# Pipeline: descarga (DANE, BIS, Wikipedia) → tablas ordenadas → DuckDB con dbt (modelos y pruebas) → análisis → pruebas.
set -euo pipefail
if [ "${SIN_DESCARGA:-0}" != "1" ]; then python ingesta/descargar.py; fi
python ingesta/preparar.py
(cd dbt && dbt build --profiles-dir . --target local)
python -W ignore -m analisis.correr
python -m pytest -q tests
