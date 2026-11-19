-- Exposición por ciudad (GEIH 2025, código AREA) con el nombre que usa el anexo del IPC.
with n(area, ciudad) as (values (5, 'Medellín'), (8, 'Barranquilla'), (11, 'Bogotá D.C.'), (13, 'Cartagena'), (15, 'Tunja'),
  (17, 'Manizales'), (18, 'Florencia'), (19, 'Popayán'), (20, 'Valledupar'), (23, 'Montería'), (27, 'Quibdo'), (41, 'Neiva'),
  (44, 'Riohacha'), (47, 'Santa Marta'), (50, 'Villavicencio'), (52, 'Pasto'), (54, 'Cúcuta'), (63, 'Armenia'), (66, 'Pereira'),
  (68, 'Bucaramanga'), (70, 'Sincelejo'), (73, 'Ibague'), (76, 'Cali'), (88, 'San Andrés'))
select n.ciudad, e.* from read_csv('{{ var("entradas") }}/exposicion_ciudad.csv') e join n on n.area = e.AREA
