SELECT
	batch_name,
	sub_location,
	feed_date,
	json_group_array (json_object(
	'feed_date', feed_date,
	 'feed_manufacturer',feed_manufacturer,
	'feed_item',feed_item,
	'feed_week',feed_week,
	'feed_additive',feed_additive,
	'feed_remark',feed_remark
	)) AS feed_details
FROM
	feed
{% if batch_name %}
WHERE
	batch_name = :batch_name
	{% if sub_location %}
	AND sub_location = :sub_location
	{% endif %}
{% elif sub_location %}
WHERE
	sub_location = :sub_location
{% endif %}
GROUP BY
	batch_name,
	sub_location,
	feed_date
ORDER BY
	feed_date DESC