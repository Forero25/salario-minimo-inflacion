{% test combinacion_unica(model, columnas) %}
select {{ columnas | join(', ') }}, count(*) n from {{ model }} group by all having count(*) > 1
{% endtest %}
