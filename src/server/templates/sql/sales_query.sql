SELECT
    sale_date,
    batch_name,
    customer,
    male_count,
    female_count,
    CASE 
        WHEN total_price IS NULL OR (male_count + female_count) = 0 THEN NULL
        ELSE total_price / (male_count + female_count)
    END as avg_price,
    CASE 
        WHEN male_count = 0 OR total_weight IS NULL THEN NULL
        ELSE ((total_weight - male_count * 0.8) / (male_count + female_count)) + 0.8
    END as male_avg_weight,
    CASE 
        WHEN female_count = 0 OR total_weight IS NULL THEN NULL
        ELSE (total_weight - male_count * 0.8) / (male_count + female_count)
    END as female_avg_weight,
    male_price,
    female_price
FROM sale
{%- if search %}
WHERE batch_name LIKE :search OR customer LIKE :search
{%- endif %}
ORDER BY sale_date DESC
LIMIT :limit OFFSET :offset