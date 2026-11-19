-- Índices mensuales por subclase (base dic. 2018 = 100) con su variación mensual.
with s as (
  select lpad(codigo::varchar, 8, '0') as codigo, subclase, ponderacion, anio, mes, indice
  from read_csv('{{ var("interim") }}/subclases.csv', types = {'codigo': 'VARCHAR'})
), c as (
  select *, coalesce(lag(indice) over (partition by codigo order by anio, mes), case when anio = 2019 and mes = 1 then 100 end) as indice_previo
  from s
)
select *, substr(codigo, 1, 4) as clase, 100 * (indice / indice_previo - 1) as var_mensual from c
