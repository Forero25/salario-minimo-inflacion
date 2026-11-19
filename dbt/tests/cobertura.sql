-- Las 188 subclases deben tener exposición (ninguna clase sin mapear) y las 24 ciudades del IPC deben estar.
select 'subclases' que, count(distinct codigo) n from {{ ref('panel_subclases') }} having count(distinct codigo) < 188
union all
select 'ciudades', count(distinct ciudad) from {{ ref('panel_ciudades') }} having count(distinct ciudad) < 24
