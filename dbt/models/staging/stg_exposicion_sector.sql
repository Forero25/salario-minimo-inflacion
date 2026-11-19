-- Exposición de cada sector (CIIU 2 dígitos) al salario mínimo, GEIH 2025. Los sectores con poca muestra se encogen
-- hacia el total nacional: E = (n·E_sector + k·E_total) / (n + k).
with s as (select lpad(RAMA2D_R4::varchar, 2, '0') as ciiu, * exclude (RAMA2D_R4) from read_csv('{{ var("entradas") }}/exposicion_sector.csv', types = {'RAMA2D_R4': 'VARCHAR'})),
t as (select * from read_csv('{{ var("entradas") }}/exposicion_total.csv'))
select s.ciiu, s.n_muestra, s.asalariados,
       (s.n_muestra * s.en_minimo + {{ var('k_encogimiento') }} * t.en_minimo) / (s.n_muestra + {{ var('k_encogimiento') }}) as en_minimo,
       (s.n_muestra * s.hasta_15 + {{ var('k_encogimiento') }} * t.hasta_15) / (s.n_muestra + {{ var('k_encogimiento') }}) as hasta_15,
       (s.n_muestra * s.en_minimo_cotizantes + {{ var('k_encogimiento') }} * t.en_minimo_cotizantes) / (s.n_muestra + {{ var('k_encogimiento') }}) as en_minimo_cotizantes,
       s.en_minimo as en_minimo_crudo
from s cross join t
