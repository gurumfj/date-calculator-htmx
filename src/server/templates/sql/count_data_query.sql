SELECT COUNT(*) FROM {{ table_name }}
{%- if event_id %}
WHERE event_id = :event_id
{%- endif %}