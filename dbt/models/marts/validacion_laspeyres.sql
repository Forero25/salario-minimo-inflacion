-- El índice total reconstruido con los índices y las ponderaciones de las 188 subclases debe coincidir con el publicado.
with r as (select anio, mes, sum(ponderacion * indice) / sum(ponderacion) as reconstruido from {{ ref('stg_subclases') }} group by all)
select r.*, t.indice as publicado, r.reconstruido - t.indice as diferencia from r join {{ ref('stg_ipc_total') }} t using (anio, mes)
