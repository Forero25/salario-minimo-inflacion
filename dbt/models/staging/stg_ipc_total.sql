select anio, mes, indice,
       100 * (indice / lag(indice) over (order by anio, mes) - 1) as var_mensual,
       100 * (indice / lag(indice, 12) over (order by anio, mes) - 1) as var_anual
from read_csv('{{ var("interim") }}/ipc_total.csv')
