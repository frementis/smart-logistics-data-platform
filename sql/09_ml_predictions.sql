
CREATE TABLE IF NOT EXISTS mart.ml_predictions (
    price_id BIGINT PRIMARY KEY
        REFERENCES core.prices(id),

    dataset_split VARCHAR(10) NOT NULL
        CHECK (dataset_split IN ('test', 'future')),

    loading_date DATE NOT NULL,
    loading_city_gcid INTEGER NOT NULL,
    unloading_city_gcid INTEGER NOT NULL,
    body_group VARCHAR(200) NOT NULL,

    actual_price_rub NUMERIC(18, 2),
    predicted_price_rub NUMERIC(18, 2) NOT NULL,

    abs_error_rub NUMERIC(18, 2),
    ape_pct NUMERIC(18, 4),

    model_name VARCHAR(100) NOT NULL,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        (dataset_split = 'future'
            AND actual_price_rub IS NULL
            AND abs_error_rub IS NULL
            AND ape_pct IS NULL)
        OR
        (dataset_split = 'test'
            AND actual_price_rub IS NOT NULL
            AND abs_error_rub IS NOT NULL
            AND ape_pct IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_ml_predictions_loading_date
    ON mart.ml_predictions(loading_date);

CREATE INDEX IF NOT EXISTS idx_ml_predictions_route
    ON mart.ml_predictions(loading_city_gcid, unloading_city_gcid);
