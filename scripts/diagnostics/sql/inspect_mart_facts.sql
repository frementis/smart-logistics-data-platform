-- Общая статистика
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT price_id) AS unique_prices,
    COUNT(DISTINCT (price_id, month_date)) AS unique_price_months,
    COUNT(DISTINCT (price_id, month_date, body_group)) AS unique_price_month_groups,
    MIN(month_date) AS first_month,
    MAX(month_date) AS last_month
FROM mart.market_price_facts;

-- Распределение по группам кузова
SELECT
    body_group,
    COUNT(*) AS rows_count,
    COUNT(DISTINCT price_id) AS unique_prices
FROM mart.market_price_facts
GROUP BY body_group
ORDER BY rows_count DESC;

-- Проверка некорректных значений
SELECT
    COUNT(*) FILTER (WHERE price_rub <= 0) AS invalid_prices,
    COUNT(*) FILTER (WHERE price_per_km <= 0) AS invalid_price_per_km,
    COUNT(*) FILTER (WHERE weight_category IS NULL) AS missing_weight_category,
    COUNT(*) FILTER (WHERE price_type NOT IN (1, 2, 3, 4, 5, 9)) AS invalid_price_types
FROM mart.market_price_facts;

-- Проверка повторов по первичному ключу
SELECT
    COUNT(*) AS duplicate_keys
FROM (
    SELECT price_id, month_date, body_group
    FROM mart.market_price_facts
    GROUP BY price_id, month_date, body_group
    HAVING COUNT(*) > 1
) duplicates;