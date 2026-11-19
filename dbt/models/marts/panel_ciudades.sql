-- Ciudad × año: inflación acumulada de enero a marzo y de julio a septiembre (placebo), desde las variaciones mensuales.
with c as (select * from {{ ref('stg_ciudades') }}),
a as (
  select ciudad, anio,
         100 * (exp(sum(ln(1 + var_mensual / 100)) filter (where mes between 1 and 3)) - 1) as var_t1,
         max(var_mensual) filter (where mes = 1) as var_ene,
         100 * (exp(sum(ln(1 + var_mensual / 100)) filter (where mes between 7 and 9)) - 1) as var_t3,
         count(*) filter (where mes between 1 and 3) n_t1, count(*) filter (where mes between 7 and 9) n_t3
  from c group by all
)
select a.*, e.en_minimo, e.hasta_15, e.en_minimo_cotizantes, e.n_muestra, sm.aumento as aumento_sm
from a join {{ ref('stg_exposicion_ciudad') }} e using (ciudad) join {{ ref('stg_salario_minimo') }} sm using (anio)
where a.n_t1 = 3
