WITH
	breed_summary AS (
		SELECT
			batch_name,
			chicken_breed,
			MIN(breed_date) AS breed_date,
			CAST((JULIANDAY('now', 'localtime') - JULIANDAY(MIN(breed_date))) AS INT) + 1 AS dayage,
			CASE
				WHEN chicken_breed = '閹雞' THEN DATE(MIN(breed_date), '+175 days')
				ELSE DATE(MIN(breed_date), '+119 days')
			END AS expire_date,
			sum(breed_male) AS total_b_male,
			sum(breed_female) AS total_b_female,
			sum(breed_male + breed_female) AS total_breed
		FROM
			breed
		WHERE
			chicken_breed = :chicken_breed
			{% if batch_name %}AND batch_name LIKE :batch_name{% endif %}
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
			b.batch_name,
			b.chicken_breed,
			b.breed_date,
			s.sales_open_date,
			s.sales_last_date,
			b.dayage,
		CASE 
			WHEN b.dayage % 7 = 0 THEN 
				(b.dayage / 7 - 1) || '/' || '7'
			ELSE 
				(b.dayage / 7) || '/' || (b.dayage % 7)
		END AS week_age,
			b.total_b_male,
			b.total_b_female,
			CAST(ROUND((b.total_b_male * 0.9 - s.total_sales_male) / 100.0) * 100 AS INT) AS sales_remain_male,
			CAST(ROUND((b.total_b_female * 0.92 - s.total_sales_female) / 100.0) * 100 AS INT) AS sales_remain_male,
			fe.feed,
			COALESCE(s.total_count, 0) AS total_count,
			CASE
				WHEN b.total_breed > 0 THEN (COALESCE(s.total_count, 0) * 100.0 / b.total_breed)
				ELSE 0
			END AS percentage,
			COALESCE(f.fcr, 0) AS fcr,
			b.expire_date
		FROM
			breed_summary b
			LEFT JOIN sale_summary s ON b.batch_name = s.batch_name
			LEFT JOIN farm_summary f ON b.batch_name = f.batch_name
			LEFT JOIN feed_summary fe ON b.batch_name = fe.batch_name
	)
SELECT
	ROW_NUMBER() OVER (
		ORDER BY
			expire_date DESC
	) AS idx,
	*
FROM
	joined
ORDER BY
	idx

{% if limit %}
LIMIT
	:limit
OFFSET
	:offset;
{% endif %}