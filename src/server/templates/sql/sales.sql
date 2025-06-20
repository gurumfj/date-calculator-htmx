WITH
	sales_summary AS (
		SELECT
			sale_date,
			batch_name,
			customer,
			male_count,
			female_count,
			total_weight,
			total_price,
			CASE
				WHEN total_price IS NULL
				OR (male_count + female_count) = 0 THEN NULL
				ELSE total_price / (male_count + female_count)
			END AS avg_price,
			CASE
				WHEN male_count = 0
				OR total_weight IS NULL THEN NULL
				ELSE ((total_weight - male_count * 0.8) / (male_count + female_count)) + 0.8
			END AS male_avg_weight,
			CASE
				WHEN female_count = 0
				OR total_weight IS NULL THEN NULL
				ELSE (total_weight - male_count * 0.8) / (male_count + female_count)
			END AS female_avg_weight,
			male_price,
			female_price
		FROM
			sale
		WHERE
			batch_name = :batch_name
			{% if sale_date %}
			AND sale_date = :sale_date
			{% endif %}
	),
	breed_info AS (
		SELECT
			batch_name,
			breed_date,
			chicken_breed,
			supplier
		FROM
			breed
		WHERE
			batch_name = :batch_name
	),
	dayage_by_date AS (
		SELECT DISTINCT
			s.sale_date,
			s.batch_name,
			json_group_array(
				json_object(
					'breed_date', b.breed_date,
					'chicken_breed', b.chicken_breed,
					'supplier', b.supplier,
					'dayage', CAST((JULIANDAY(s.sale_date) - JULIANDAY(b.breed_date)) AS INT) + 1
				)
			) AS dayage_details
		FROM
			(SELECT DISTINCT sale_date, batch_name FROM sales_summary) s
		CROSS JOIN breed_info b
		GROUP BY
			s.sale_date,
			s.batch_name
	)
SELECT
	s.sale_date,
	s.batch_name,
	sum(s.male_count) as daily_male_count,
	sum(s.female_count) as daily_female_count,
	sum(s.male_count + s.female_count) as daily_total_count,
	COALESCE(sum(s.total_weight), 0) as daily_total_weight,
	COALESCE(sum(s.total_price), 0) as daily_total_price,
	CASE
		WHEN sum(s.male_count + s.female_count) > 0 THEN 
			sum(s.total_price) / sum(s.male_count + s.female_count)
		ELSE NULL
	END AS daily_avg_price,
	d.dayage_details,
	json_group_array(
		json_object(
			'customer', s.customer,
			'male_count', s.male_count,
			'female_count', s.female_count,
			'total_weight', s.total_weight,
			'total_price', s.total_price,
			'avg_price', s.avg_price,
			'male_price', s.male_price,
			'female_price', s.female_price
		)
	) AS sales_details
FROM
	sales_summary s
LEFT JOIN dayage_by_date d ON s.sale_date = d.sale_date AND s.batch_name = d.batch_name
GROUP BY
	s.sale_date,
	s.batch_name,
	d.dayage_details
ORDER BY
	s.sale_date DESC