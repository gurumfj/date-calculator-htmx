SELECT * FROM {{ table_name }}
{%- if event_id %}
WHERE event_id = :event_id
{%- endif %}
{%- if sort_by_column %}
ORDER BY {{ sort_by_column }} {{ sort_order or 'DESC' }}
{%- else %}
  {%- if table_name == 'breed' %}
ORDER BY breed_date DESC
  {%- elif table_name == 'sale' %}
ORDER BY sale_date DESC
  {%- elif table_name == 'feed' %}
ORDER BY feed_date DESC
  {%- elif table_name == 'farm_production' %}
ORDER BY created_at DESC
  {%- elif table_name == 'events' %}
ORDER BY upload_timestamp DESC
  {%- endif %}
{%- endif %}
{%- if pagination %}
LIMIT :page_size OFFSET :offset
{%- endif %}