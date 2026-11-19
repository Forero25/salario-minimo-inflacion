-- Aumento del salario mínimo de cada año (calculado con los niveles, no con la columna de variación de la tabla).
select anio, smmlv, aumento from read_csv('{{ var("interim") }}/salario_minimo.csv') where anio >= 2000
