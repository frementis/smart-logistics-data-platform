BEGIN;

DELETE FROM mart.market_prices;

WITH aggregated AS (
    SELECT
        month_date,
        loading_city_gcid,
        unloading_city_gcid,
        body_group,
        weight_category,

        COUNT(DISTINCT price_id) AS trips_count,

        COUNT(DISTINCT organization_id)
            FILTER (WHERE price_type IN (3, 9)) AS carriers_count,

        AVG(price_rub)::NUMERIC(18, 2) AS avg_price_rub,

        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY price_rub)::NUMERIC(18, 2)
            AS p25_price_rub,

        PERCENTILE_CONT(0.50)
            WITHIN GROUP (ORDER BY price_rub)::NUMERIC(18, 2)
            AS p50_price_rub,

        PERCENTILE_CONT(0.75)
            WITHIN GROUP (ORDER BY price_rub)::NUMERIC(18, 2)
            AS p75_price_rub,

        AVG(price_per_km)::NUMERIC(18, 2) AS avg_price_per_km,

        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY price_per_km)::NUMERIC(18, 2)
            AS p25_price_per_km,

        PERCENTILE_CONT(0.50)
            WITHIN GROUP (ORDER BY price_per_km)::NUMERIC(18, 2)
            AS p50_price_per_km,

        PERCENTILE_CONT(0.75)
            WITHIN GROUP (ORDER BY price_per_km)::NUMERIC(18, 2)
            AS p75_price_per_km,

        (
            STDDEV_SAMP(price_rub)
            / NULLIF(AVG(price_rub), 0)
        )::NUMERIC(18, 4) AS cv_price,

        (DATE '2026-10-26' - month_date) AS freshness_days

    FROM mart.market_price_facts
    GROUP BY
        month_date,
        loading_city_gcid,
        unloading_city_gcid,
        body_group,
        weight_category
),

with_changes AS (
    SELECT
        current_month.*,

        (
            100.0 * (
                current_month.avg_price_rub - previous_month.avg_price_rub
            ) / NULLIF(previous_month.avg_price_rub, 0)
        )::NUMERIC(18, 4) AS mom_change_pct,

        (
            100.0 * (
                current_month.avg_price_rub - previous_year.avg_price_rub
            ) / NULLIF(previous_year.avg_price_rub, 0)
        )::NUMERIC(18, 4) AS yoy_change_pct

    FROM aggregated current_month

    LEFT JOIN aggregated previous_month
        ON previous_month.month_date =
            (current_month.month_date - INTERVAL '1 month')::DATE
        AND previous_month.loading_city_gcid =
            current_month.loading_city_gcid
        AND previous_month.unloading_city_gcid =
            current_month.unloading_city_gcid
        AND previous_month.body_group =
            current_month.body_group
        AND previous_month.weight_category =
            current_month.weight_category

    LEFT JOIN aggregated previous_year
        ON previous_year.month_date =
            (current_month.month_date - INTERVAL '1 year')::DATE
        AND previous_year.loading_city_gcid =
            current_month.loading_city_gcid
        AND previous_year.unloading_city_gcid =
            current_month.unloading_city_gcid
        AND previous_year.body_group =
            current_month.body_group
        AND previous_year.weight_category =
            current_month.weight_category
)

INSERT INTO mart.market_prices (
    month_date,
    loading_city_gcid,
    unloading_city_gcid,
    body_group,
    weight_category,
    trips_count,
    carriers_count,
    avg_price_rub,
    p25_price_rub,
    p50_price_rub,
    p75_price_rub,
    avg_price_per_km,
    p25_price_per_km,
    p50_price_per_km,
    p75_price_per_km,
    cv_price,
    mom_change_pct,
    yoy_change_pct,
    reliability,
    freshness_days
)
SELECT
    month_date,
    loading_city_gcid,
    unloading_city_gcid,
    body_group,
    weight_category,
    trips_count,
    carriers_count,
    avg_price_rub,
    p25_price_rub,
    p50_price_rub,
    p75_price_rub,
    avg_price_per_km,
    p25_price_per_km,
    p50_price_per_km,
    p75_price_per_km,
    cv_price,
    mom_change_pct,
    yoy_change_pct,

    CASE
        WHEN trips_count >= 30
            AND carriers_count >= 5
            AND freshness_days <= 30
            THEN 'HIGH'
        WHEN trips_count >= 10
            THEN 'MEDIUM'
        ELSE 'LOW_DATA'
    END AS reliability,

    freshness_days

FROM with_changes;

COMMIT;