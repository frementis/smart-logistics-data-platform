BEGIN;

CREATE TABLE IF NOT EXISTS mart.dim_city (
    gc_id INTEGER PRIMARY KEY,
    city_name TEXT,
    full_name_local TEXT,
    full_name_gc TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS mart.dim_month (
    month_date DATE PRIMARY KEY,
    calendar_year SMALLINT NOT NULL,
    month_number SMALLINT NOT NULL,
    quarter_number SMALLINT NOT NULL,
    month_label VARCHAR(7) NOT NULL
);

CREATE TABLE IF NOT EXISTS mart.dim_body_group (
    body_group VARCHAR(30) PRIMARY KEY,
    sort_order SMALLINT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS mart.dim_weight_category (
    weight_category VARCHAR(4) PRIMARY KEY,
    sort_order SMALLINT NOT NULL,
    min_weight_t NUMERIC(8, 2) NOT NULL,
    max_weight_t NUMERIC(8, 2)
);

-- Города: оставляем одну запись на gc_id.
-- При дублях выбираем запись с минимальным id.


INSERT INTO mart.dim_city (
    gc_id,
    city_name,
    full_name_local,
    full_name_gc,
    longitude,
    latitude
)
SELECT DISTINCT ON (gc_id)
    gc_id,
    name,
    full_name_local,
    full_name_gc,
    longitude,
    latitude
FROM public.cities
ORDER BY gc_id, id
ON CONFLICT (gc_id) DO UPDATE
SET
    city_name = EXCLUDED.city_name,
    full_name_local = EXCLUDED.full_name_local,
    full_name_gc = EXCLUDED.full_name_gc,
    longitude = EXCLUDED.longitude,
    latitude = EXCLUDED.latitude;;

-- Календарное измерение: все месяцы между
-- первой и последней датами фактов.


INSERT INTO mart.dim_month (
    month_date,
    calendar_year,
    month_number,
    quarter_number,
    month_label
)
SELECT
    month_date::DATE,
    EXTRACT(YEAR FROM month_date)::SMALLINT,
    EXTRACT(MONTH FROM month_date)::SMALLINT,
    EXTRACT(QUARTER FROM month_date)::SMALLINT,
    TO_CHAR(month_date, 'YYYY-MM')
FROM GENERATE_SERIES(
    (SELECT MIN(month_date) FROM mart.market_price_facts),
    (SELECT MAX(month_date) FROM mart.market_price_facts),
    INTERVAL '1 month'
) AS month_date
ON CONFLICT (month_date) DO UPDATE
SET
    calendar_year = EXCLUDED.calendar_year,
    month_number = EXCLUDED.month_number,
    quarter_number = EXCLUDED.quarter_number,
    month_label = EXCLUDED.month_label;;

-- Измерение групп кузова.
INSERT INTO mart.dim_body_group (
    body_group,
    sort_order,
    description
)
SELECT DISTINCT
    body_group,
    CASE body_group
        WHEN U&'\0422\0435\043D\0442' THEN 1
        WHEN U&'\0420\0435\0444\0440\0438\0436\0435\0440\0430\0442\043E\0440' THEN 2
        WHEN U&'\0418\0437\043E\0442\0435\0440\043C' THEN 3
        WHEN U&'\0411\043E\0440\0442' THEN 4
        WHEN U&'\041F\0440\043E\0447\0438\0435' THEN 5
        WHEN U&'\041D\0435\0020\0443\043A\0430\0437\0430\043D' THEN 6
    END,
    CASE body_group
        WHEN U&'\0422\0435\043D\0442' THEN 'Tent'
        WHEN U&'\0420\0435\0444\0440\0438\0436\0435\0440\0430\0442\043E\0440' THEN 'Refrigerated'
        WHEN U&'\0418\0437\043E\0442\0435\0440\043C' THEN 'Insulated'
        WHEN U&'\0411\043E\0440\0442' THEN 'Flatbed'
        WHEN U&'\041F\0440\043E\0447\0438\0435' THEN 'Other'
        WHEN U&'\041D\0435\0020\0443\043A\0430\0437\0430\043D' THEN 'Not specified'
    END
FROM mart.market_price_facts
ON CONFLICT (body_group) DO UPDATE
SET
    sort_order = EXCLUDED.sort_order,
    description = EXCLUDED.description;

-- Измерение категорий веса.
INSERT INTO mart.dim_weight_category (
    weight_category,
    sort_order,
    min_weight_t,
    max_weight_t
)
VALUES
    ('G20T', 1, 30.00, NULL),
    ('FTL', 2, 10.00, 30.00),
    ('10T', 3, 5.00, 10.00),
    ('5T', 4, 2.50, 5.00),
    ('L5T', 5, 0.50, 2.50),
    ('OTH', 6, 0.00, 0.50)
ON CONFLICT (weight_category) DO UPDATE
SET
    sort_order = EXCLUDED.sort_order,
    min_weight_t = EXCLUDED.min_weight_t,
    max_weight_t = EXCLUDED.max_weight_t;

COMMIT;