-- 1. Какие поля доступны в справочнике городов?
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'cities'
ORDER BY ordinal_position;

-- 2. Какие поля доступны в Core?
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'core'
  AND table_name = 'prices'
ORDER BY ordinal_position;

-- 3. Сколько записей подходит для ML по основным условиям?
SELECT
    COUNT(*) AS eligible_records,
    COUNT(*) FILTER (
        WHERE loading_date >= DATE '2026-07-26'
          AND loading_date < DATE '2026-10-05'
    ) AS train_records,
    COUNT(*) FILTER (
        WHERE loading_date >= DATE '2026-10-05'
          AND loading_date <= DATE '2026-10-26'
    ) AS test_records,
    COUNT(*) FILTER (
        WHERE loading_date > DATE '2026-10-26'
    ) AS future_records,
    MIN(loading_date) AS first_loading_date,
    MAX(loading_date) AS last_loading_date
FROM core.prices
WHERE is_fact IS TRUE
  AND complex IS FALSE
  AND price_rub > 0
  AND distance > 0
  AND outlier_mark IS FALSE;

-- 4. Проверяем пропуски в основных признаках
SELECT
    COUNT(*) FILTER (WHERE total_weight IS NULL) AS missing_weight,
    COUNT(*) FILTER (WHERE total_volume IS NULL) AS missing_volume,
    COUNT(*) FILTER (WHERE loading_city_gcid IS NULL) AS missing_loading_city,
    COUNT(*) FILTER (WHERE unloading_city_gcid IS NULL) AS missing_unloading_city,
    COUNT(*) FILTER (WHERE loading_date IS NULL) AS missing_loading_date,
    COUNT(*) FILTER (WHERE core_weight_category IS NULL) AS missing_weight_category,
    COUNT(*) FILTER (WHERE core_volume_category IS NULL) AS missing_volume_category
FROM core.prices
WHERE is_fact IS TRUE
  AND complex IS FALSE
  AND price_rub > 0
  AND distance > 0
  AND outlier_mark IS FALSE;