SELECT 
    batch_name, chicken_breed,
    SUM(breed_male) AS male,
    SUM(breed_female) AS female,
    MIN(breed_date) AS breed_date,
    DATE(breed_date, '+120 days') AS expire_date,
    COUNT(batch_name) AS count
FROM breed 
WHERE is_completed = 0 
GROUP BY batch_name 
ORDER BY expire_date DESC