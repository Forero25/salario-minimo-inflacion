# Método

## 1. Datos

| Fuente | Qué trae | Periodo |
|---|---|---|
| DANE, anexos del IPC | Índice mensual de 188 subclases (base dic. 2018 = 100) con su ponderación | 2019-2026 |
| DANE, anexos del IPC | Variación mensual de 24 ciudades | 2017-2026 |
| DANE, serie empalmada | Índice total | 2003-2026 |
| GEIH 2025 | Asalariados por rango de ingreso, por sector (CIIU 2 dígitos) y por ciudad | 2025 |
| BIS | Inflación anual de 26 países | 2021-2026 |
| Wikipedia | Salario mínimo mensual de cada año | 2000-2026 |

**Validación.** Con un índice de Laspeyres de base fija, el índice total es el promedio de los índices de las subclases ponderado por sus
ponderaciones. La reconstrucción coincide con el índice publicado en los 94 meses con una diferencia máxima de 0,04 puntos (prueba de dbt).

## 2. Exposición al salario mínimo (GEIH 2025)

Asalariados (empleados particulares, del gobierno y domésticos) con ingreso mensual del empleo principal. "En el mínimo": entre 0,95 y 1,05
SMMLV de 2025 ($1.423.500). Variantes: entre 0,95 y 1,5 SMMLV, y en el mínimo cotizando a pensión. Factor de expansión mensual / 12.
El cálculo corre en el computador donde están los microdatos (`geih/exposicion.py`) y solo guarda agregados en `entradas/`.

Los sectores con poca muestra se encogen hacia el total nacional: E = (n·E_sector + 100·E_total) / (n + 100).

## 3. Aumento real

Aumento nominal del mínimo menos la inflación de diciembre del año anterior. Es la parte del aumento que no es indexación a la inflación pasada.

## 4. Diseño por ciudades

Para la ciudad *c* y el año *t* (2017-2026):

inflación de enero a marzo(c, t) = α_c + γ_t + β · aumento real(t) · exposición(c) + error

α_c quita lo que cada ciudad tiene de distinto todo el tiempo; γ_t quita lo que le pasa a todo el país cada año. β dice cuántos puntos más de
inflación tiene una ciudad por cada punto de aumento real del mínimo, si todos sus asalariados estuvieran en el mínimo. Errores agrupados por ciudad.

*Ejemplo:* con β = 0,165, un aumento real de 17,9 puntos y una diferencia de exposición de 0,31 (Armenia frente a Florencia), la diferencia
esperada en la inflación de enero a marzo es 0,165 × 17,9 × 0,31 ≈ 0,9 puntos.

**Robustez:** solo enero; aumento nominal; otras dos exposiciones; sin 2026; placebo con julio a septiembre; quitando una ciudad a la vez;
inferencia por permutación (2.000 repartos al azar de las exposiciones entre ciudades); pendiente mes a mes en 2026 y en 2025.

## 5. Diseño por productos

El mismo modelo entre subclases, con la exposición del sector que produce cada una (mapa clase COICOP → CIIU en `entradas/mapa_clases.csv`).
Se excluye el arriendo imputado. Variantes: sin ponderar, sin alimentos ni regulados, exposición hasta 1,5 mínimos y placebo.

## 6. Control sintético

Pesos no negativos que suman 1 sobre la inflación anual de 22 países para reproducir la de Colombia entre enero de 2023 y diciembre de 2025.
La brecha después de 2026 se compara con la de placebos: el mismo ejercicio tratando a cada país como el tratado; se ordena por la razón
entre el error después y el error antes.

## 7. Reproducibilidad

Python descarga y ordena, dbt modela en DuckDB con 18 pruebas, Python analiza con 3 pruebas (una verifica con datos simulados que el diseño
por ciudades recupera un efecto conocido y no inventa uno). Todo en Docker, en GitHub Actions cada mes. Resultados deterministas.
