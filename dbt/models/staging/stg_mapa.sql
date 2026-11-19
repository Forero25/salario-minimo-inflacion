select lpad(clase::varchar, 4, '0') as clase, lpad(ciiu::varchar, 2, '0') as ciiu, tipo, marca, nota
from read_csv('{{ var("entradas") }}/mapa_clases.csv', types = {'clase': 'VARCHAR', 'ciiu': 'VARCHAR'})
