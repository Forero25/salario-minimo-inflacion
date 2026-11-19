FROM python:3.12-slim
WORKDIR /app
COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt
COPY ingesta ingesta
COPY dbt dbt
COPY analisis analisis
COPY tests tests
COPY entradas entradas
COPY correr.sh .
ENV SM_DB=/app/data/salario.duckdb SM_INTERIM=/app/data/interim SM_ENTRADAS=/app/entradas PYTHONWARNINGS=ignore
CMD ["bash", "correr.sh"]
