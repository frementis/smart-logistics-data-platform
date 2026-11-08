BEGIN;

-- Очищаем таблицу перед полной пересборкой.
-- DELETE внутри транзакции позволяет откатить операцию при ошибке.
DELETE FROM mart.market_price_facts;

WITH canonical_cities AS (
    SELECT
        gc_id,
        MIN(id) AS city_id
    FROM public.cities
    GROUP BY gc_id
)

INSERT INTO mart.market_price_facts (
    price_id,
    month_date,
    loading_city_gcid,
    unloading_city_gcid,
    body_group,
    weight_category,
    organization_id,
    price_rub,
    price_per_km,
    price_type
)
SELECT
    cp.id,
    DATE_TRUNC('month', pd.price_date)::DATE,
    loading_city.gc_id,
    unloading_city.gc_id,
    pbg.body_group,
    cp.core_weight_category,
    cp.organization_id,
    cp.price_rub,
    (cp.price_rub / NULLIF(cp.distance, 0))::NUMERIC(18, 4),
    cp.price_type
FROM core.prices cp
JOIN public.price_dates pd
    ON pd.price_id = cp.id
JOIN core.price_body_groups pbg
    ON pbg.price_id = cp.id
JOIN canonical_cities loading_city
    ON loading_city.gc_id = cp.loading_city_gcid
JOIN canonical_cities unloading_city
    ON unloading_city.gc_id = cp.unloading_city_gcid
WHERE
    cp.is_fact IS TRUE
    AND cp.price_type IN (1, 2, 3, 4, 5, 9)
    AND cp.complex IS FALSE
    AND cp.price_rub > 0
    AND cp.distance > 0
    AND cp.outlier_mark IS FALSE
    AND pd.price_date <= DATE '2026-10-26';

COMMIT;