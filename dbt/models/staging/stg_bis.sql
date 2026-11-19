select pais, anio, mes, inflacion_anual from read_csv('{{ var("interim") }}/bis.csv') where anio >= 2015
