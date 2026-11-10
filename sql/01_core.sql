
-- Схема Core DWH
CREATE SCHEMA IF NOT EXISTS core;

-- Таблица истории запусков ETL
CREATE TABLE IF NOT EXISTS core.etl_batches (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    date_from DATE,
    date_to DATE,
    source_count BIGINT DEFAULT 0,
    loaded_count BIGINT DEFAULT 0,
    quarantined_count BIGINT DEFAULT 0,
    error_message TEXT
);

-- Основная таблица Core на основе  prices

CREATE TABLE IF NOT EXISTS core.prices AS
SELECT
    p.*,
    NULL::NUMERIC(18, 2) AS price_rub,
    NULL::VARCHAR(4) AS core_weight_category,
    NULL::VARCHAR(4) AS core_volume_category,
    CURRENT_TIMESTAMP AS processed_at,
    NULL::BIGINT AS batch_id
FROM public.prices p
WHERE FALSE;

-- Первичный ключ
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'core.prices'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE core.prices
            ADD CONSTRAINT core_prices_pkey PRIMARY KEY (id);
    END IF;
END
$$;

-- Таблица некорректных записей
CREATE TABLE IF NOT EXISTS core.dq_quarantine_prices (
    price_id BIGINT PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    reason_code VARCHAR(100) NOT NULL,
    reason_detail TEXT,
    source_record JSONB NOT NULL,
    quarantined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_core_prices_loading_date
    ON core.prices (loading_date);

CREATE INDEX IF NOT EXISTS idx_core_prices_route
    ON core.prices (loading_city_gcid, unloading_city_gcid);

CREATE INDEX IF NOT EXISTS idx_core_quarantine_batch
    ON core.dq_quarantine_prices (batch_id);
