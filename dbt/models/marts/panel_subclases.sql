-- Subclase × año: variación del primer trimestre (dic. anterior a marzo) y del tercer trimestre (jun. a sep., placebo),
-- con la exposición al salario mínimo de su sector y el aumento del salario mínimo de ese año.
with s as (select * from {{ ref('stg_subclases') }}),
dic as (select codigo, anio + 1 as anio, indice as ind_dic from s where mes = 12
        union all select distinct codigo, 2019, 100.0 from s),
p as (
  select s.codigo, any_value(s.subclase) subclase, any_value(s.clase) clase, any_value(s.ponderacion) ponderacion, s.anio,
         max(s.indice) filter (where s.mes = 1) ind_ene, max(s.indice) filter (where s.mes = 3) ind_mar,
         max(s.indice) filter (where s.mes = 6) ind_jun, max(s.indice) filter (where s.mes = 9) ind_sep
  from s group by s.codigo, s.anio
)
select p.codigo, p.subclase, p.clase, p.ponderacion, p.anio, m.tipo, m.marca, m.ciiu,
       100 * (p.ind_ene / d.ind_dic - 1) as var_ene, 100 * (p.ind_mar / d.ind_dic - 1) as var_t1, 100 * (p.ind_sep / p.ind_jun - 1) as var_t3,
       e.en_minimo, e.hasta_15, e.en_minimo_cotizantes, sm.aumento as aumento_sm
from p join dic d using (codigo, anio)
join {{ ref('stg_mapa') }} m on m.clase = p.clase
join {{ ref('stg_exposicion_sector') }} e on e.ciiu = m.ciiu
join {{ ref('stg_salario_minimo') }} sm on sm.anio = p.anio
