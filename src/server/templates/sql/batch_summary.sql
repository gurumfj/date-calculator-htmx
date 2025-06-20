WITH
	breed_dayage AS (
		SELECT
			*,
			CAST((JULIANDAY('now', 'localtime') - JULIANDAY(breed_date)) AS INT) + 1 AS dayage
		FROM
			breed
	),
	breed_details AS (
		SELECT
			*,
			CASE
				WHEN dayage % 7 = 0 THEN (dayage / 7 - 1) || '/' || '7'
				ELSE (dayage / 7) || '/' || (dayage % 7)
			END AS week_age
		FROM
			breed_dayage
	),
	breed_summary AS (
		SELECT
			batch_name,
			chicken_breed,
			sum(breed_male) AS total_b_male,
			sum(breed_female) AS total_b_female,
			max(dayage) AS dayage,
			MAX(week_age) AS weekage,
			count(batch_name) AS batch_count,
			sum(breed_male + breed_female) AS total_breed,
			json_group_array(json_object('chicken_breed', chicken_breed, 'breed_date', breed_date, 'day_age', dayage, 'week_age', week_age, 'supplier', supplier)) AS breed_details
		FROM
			breed_details
		WHERE
			{% if batch_name %}
			batch_name LIKE :batch_name
			{% else %}
			chicken_breed = :chicken_breed
			{% endif %}
		GROUP BY
			batch_name,
			chicken_breed
	),
	sale_summary AS (
		SELECT
			batch_name,
			sum(male_count) AS total_sales_male,
			sum(female_count) AS total_sales_female,
			SUM(male_count + female_count) AS total_count,
			min(sale_date) AS sales_open_date,
			max(sale_date) AS sales_last_date
		FROM
			sale
		GROUP BY
			batch_name
	),
	farm_summary AS (
		SELECT
			batch_name,
			fcr
		FROM
			farm_production
	),
	feed_summary AS (
		SELECT
			batch_name,
			GROUP_CONCAT(DISTINCT feed_manufacturer) AS feed
		FROM
			feed
		GROUP BY
			batch_name
	),
	joined AS (
		SELECT
			ROW_NUMBER() OVER (
				ORDER BY
					b.dayage asc
			) AS idx,
			b.batch_name,
			b.chicken_breed,
			b.dayage,
			b.weekage,
			b.batch_count,
			b.total_b_male,
			b.total_b_female,
			total_sales_male,
			total_sales_female,
			s.sales_open_date,
			s.sales_last_date,			
			CAST(ROUND((b.total_b_male * 0.9 - s.total_sales_male) / 100.0) * 100 AS INT) AS sales_remain_male,
			CAST(ROUND((b.total_b_female * 0.92 - s.total_sales_female) / 100.0) * 100 AS INT) AS sales_remain_female,
			fe.feed,
			COALESCE(s.total_count, 0) AS total_count,
			CASE
				WHEN b.total_breed > 0 THEN (COALESCE(s.total_count, 0) * 100.0 / b.total_breed)
				ELSE 0
			END AS percentage,
			COALESCE(f.fcr, 0) AS fcr,
			breed_details
		FROM
			breed_summary b
			LEFT JOIN sale_summary s ON b.batch_name = s.batch_name
			LEFT JOIN farm_summary f ON b.batch_name = f.batch_name
			LEFT JOIN feed_summary fe ON b.batch_name = fe.batch_name
	)
SELECT
	*
FROM
	joined
WHERE
	idx > :offset
LIMIT
	:limit

