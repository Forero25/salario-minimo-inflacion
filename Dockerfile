FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt
COPY ingesta ingesta
COPY dbt dbt
COPY analisis analisis
COPY tests tests
COPY entradas entradas
COPY correr.sh .
ENV SM_DB=/app/data/salario.duckdb SM_INTERIM=/app/data/interim SM_ENTRADAS=/app/entradas SM_BOLETINES=/app/data/raw/boletines PYTHONWARNINGS=ignore
CMD ["bash", "correr.sh"]
