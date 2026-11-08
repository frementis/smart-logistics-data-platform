
import pandas as pd
from sqlalchemy import text

from etl.db import engine


ML_DATASET_QUERY = text("""
WITH canonical_cities AS (
    SELECT DISTINCT ON (gc_id)
        gc_id,
        TRIM(SPLIT_PART(full_name_local, ',', 1)) AS city_name,
        CASE
            WHEN TRIM(SPLIT_PART(full_name_local, ',', 2)) LIKE 'г. %%'
                THEN TRIM(SUBSTRING(
                    TRIM(SPLIT_PART(full_name_local, ',', 2)) FROM 4
                ))
            ELSE TRIM(SPLIT_PART(full_name_local, ',', 2))
        END AS region_name,
        longitude,
        latitude
    FROM public.cities
    ORDER BY gc_id, id
),
body_groups AS (
    SELECT
        price_id,
        STRING_AGG(DISTINCT body_group, '|' ORDER BY body_group) AS body_group
    FROM core.price_body_groups
    GROUP BY price_id
),
eligible_prices AS (
    SELECT
        cp.*,
        CASE
            WHEN cp.loading_date >= DATE '2026-07-26'
             AND cp.loading_date < DATE '2026-10-05'
                THEN 'train'
            WHEN cp.loading_date >= DATE '2026-10-05'
             AND cp.loading_date <= DATE '2026-10-26'
                THEN 'test'
            WHEN cp.loading_date > DATE '2026-10-26'
                THEN 'future'
        END AS dataset_split
    FROM core.prices cp
    WHERE cp.is_fact IS TRUE
      AND cp.complex IS FALSE
      AND cp.price_rub > 0
      AND cp.distance > 0
      AND cp.outlier_mark IS FALSE
      AND (
          cp.loading_date >= DATE '2026-07-26'
          AND cp.loading_date <= DATE '2026-10-26'
          OR cp.loading_date > DATE '2026-10-26'
      )
)
SELECT
    p.id AS price_id,
    p.dataset_split,
    p.loading_date,

    origin.gc_id AS loading_city_gcid,
    origin.city_name AS loading_city,
    origin.region_name AS loading_region,
    origin.longitude AS loading_longitude,
    origin.latitude AS loading_latitude,

    destination.gc_id AS unloading_city_gcid,
    destination.city_name AS unloading_city,
    destination.region_name AS unloading_region,
    destination.longitude AS unloading_longitude,
    destination.latitude AS unloading_latitude,

    p.distance,
    p.total_weight,
    p.total_volume,

    bg.body_group,
    p.core_weight_category AS weight_category,
    p.core_volume_category AS volume_category,

    EXTRACT(YEAR FROM p.loading_date)::INTEGER AS loading_year,
    EXTRACT(MONTH FROM p.loading_date)::INTEGER AS loading_month,
    EXTRACT(ISODOW FROM p.loading_date)::INTEGER AS loading_weekday,
    EXTRACT(DOY FROM p.loading_date)::INTEGER AS loading_day_of_year,

    SIN(2 * PI() * EXTRACT(MONTH FROM p.loading_date) / 12.0)
        AS month_sin,
    COS(2 * PI() * EXTRACT(MONTH FROM p.loading_date) / 12.0)
        AS month_cos,

    SIN(2 * PI() * (EXTRACT(ISODOW FROM p.loading_date) - 1) / 7.0)
        AS weekday_sin,
    COS(2 * PI() * (EXTRACT(ISODOW FROM p.loading_date) - 1) / 7.0)
        AS weekday_cos,

    SIN(2 * PI() * (EXTRACT(DOY FROM p.loading_date) - 1) / 365.25)
        AS day_of_year_sin,
    COS(2 * PI() * (EXTRACT(DOY FROM p.loading_date) - 1) / 365.25)
        AS day_of_year_cos,

    CASE
        WHEN p.dataset_split IN ('train', 'test')
            THEN p.price_rub
        ELSE NULL
    END AS target_price_rub

FROM eligible_prices p
JOIN canonical_cities origin
    ON origin.gc_id = p.loading_city_gcid
JOIN canonical_cities destination
    ON destination.gc_id = p.unloading_city_gcid
JOIN body_groups bg
    ON bg.price_id = p.id
ORDER BY p.loading_date, p.id
""")


def extract_ml_dataset() -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql_query(ML_DATASET_QUERY, connection)
