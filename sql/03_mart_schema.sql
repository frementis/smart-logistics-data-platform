CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.market_prices (
    month_date DATE NOT NULL,

    loading_city_gcid INTEGER NOT NULL,
    unloading_city_gcid INTEGER NOT NULL,

    body_group VARCHAR(30) NOT NULL,
    weight_category VARCHAR(4) NOT NULL,

    -- Количество перевозок и перевозчиков
    trips_count BIGINT NOT NULL,
    carriers_count BIGINT NOT NULL,

    -- Стоимость перевозки в рублях
    avg_price_rub NUMERIC(18, 2),
    p25_price_rub NUMERIC(18, 2),
    p50_price_rub NUMERIC(18, 2),
    p75_price_rub NUMERIC(18, 2),

    -- Стоимость одного километра
    avg_price_per_km NUMERIC(18, 2),
    p25_price_per_km NUMERIC(18, 2),
    p50_price_per_km NUMERIC(18, 2),
    p75_price_per_km NUMERIC(18, 2),

    -- Коэффициент вариации
    cv_price NUMERIC(18, 4),

    -- Изменение медианной цены
    mom_change_pct NUMERIC(18, 4),
    yoy_change_pct NUMERIC(18, 4),

    -- Надёжность данных
    reliability VARCHAR(10) NOT NULL,
    freshness_days INTEGER,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        month_date,
        loading_city_gcid,
        unloading_city_gcid,
        body_group,
        weight_category
    ),

    CHECK (reliability IN ('HIGH', 'MEDIUM', 'LOW_DATA'))
);

CREATE INDEX IF NOT EXISTS idx_market_prices_month
    ON mart.market_prices(month_date);

CREATE INDEX IF NOT EXISTS idx_market_prices_route
    ON mart.market_prices(
        loading_city_gcid,
        unloading_city_gcid
    );