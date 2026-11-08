-- 1. Количество записей в измерениях
SELECT 'dim_city' AS dimension, COUNT(*) AS rows_count
FROM mart.dim_city
UNION ALL
SELECT 'dim_month', COUNT(*)
FROM mart.dim_month
UNION ALL
SELECT 'dim_body_group', COUNT(*)
FROM mart.dim_body_group
UNION ALL
SELECT 'dim_weight_category', COUNT(*)
FROM mart.dim_weight_category;

-- 2. Группы кузова
SELECT *
FROM mart.dim_body_group
ORDER BY sort_order;

-- 3. Категории веса
SELECT *
FROM mart.dim_weight_category
ORDER BY sort_order;

-- 4. Проверка диапазона календаря
SELECT
    MIN(month_date) AS first_month,
    MAX(month_date) AS last_month,
    COUNT(*) AS months_count
FROM mart.dim_month;