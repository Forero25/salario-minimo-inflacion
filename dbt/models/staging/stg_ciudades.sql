select ciudad, anio, mes, var_mensual from read_csv('{{ var("interim") }}/ciudades.csv')
where ciudad not in ('Total IPC', 'Otras áreas urbanas')
