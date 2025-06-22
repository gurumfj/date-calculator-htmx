SELECT
    batch_name,
    farm_location,
    farmer,
    chick_in_count,
    chicken_out_count,
    feed_weight,
    sale_weight_jin,
    fcr,
    meat_cost,
    CASE
    	WHEN revenue >0 and sale_weight_jin >0 THEN
    		ROUND(revenue/sale_weight_jin,2)
		else 0
	END as avg_price,
    CASE
    	WHEN ABS(expenses) >0 and sale_weight_jin >0 THEN
    		ROUND(ABS(expenses)/sale_weight_jin,2)
		else 0
	END as cost_price,
    revenue,
    expenses,
    feed_cost,
    vet_cost,
    feed_med_cost,
    farm_med_cost,
    leg_band_cost,
    chick_cost,
    grow_fee,
    catch_fee,
    weigh_fee,
    gas_cost,
    -- 計算衍生指標
    CASE 
        WHEN chick_in_count > 0 THEN 
            ROUND((chicken_out_count * 100.0 / chick_in_count), 2)
        ELSE 0 
    END AS survival_rate,
    CASE 
        WHEN expenses != 0 THEN 
            ROUND((revenue + expenses), 2)
        ELSE 0 
    END AS profit,
    CASE 
        WHEN revenue > 0 THEN 
            ROUND(((revenue + expenses) * 100.0 / revenue), 2)
        ELSE 0 
    END AS profit_margin,
    CASE 
        WHEN chicken_out_count > 0 AND sale_weight_jin > 0 THEN 
            ROUND((sale_weight_jin / chicken_out_count), 2)
        ELSE 0 
    END AS avg_weight_per_chicken,
    created_at
FROM
    farm_production
{% if batch_name %}
WHERE
    batch_name = :batch_name
{% endif %}
ORDER BY
    created_at DESC