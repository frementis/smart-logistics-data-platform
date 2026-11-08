CREATE TABLE IF NOT EXISTS mart.market_price_facts (
    price_id BIGINT NOT NULL,
    month_date DATE NOT NULL,

    loading_city_gcid INTEGER NOT NULL,
    unloading_city_gcid INTEGER NOT NULL,

    body_group VARCHAR(30) NOT NULL,
    weight_category VARCHAR(4) NOT NULL,

    organization_id INTEGER,
    price_type SMALLINT,

    price_rub NUMERIC(18, 2) NOT NULL,
    price_per_km NUMERIC(18, 4) NOT NULL,

    PRIMARY KEY (price_id, month_date, body_group)
);

CREATE INDEX IF NOT EXISTS idx_market_facts_month
    ON mart.market_price_facts(month_date);

CREATE INDEX IF NOT EXISTS idx_market_facts_route
    ON mart.market_price_facts(
        loading_city_gcid,
        unloading_city_gcid
    );