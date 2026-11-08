
import pandas as pd
from sqlalchemy import text

from etl.db import engine


query = text("""
    SELECT
        COUNT(*) AS total_prices,

        COUNT(*) FILTER (
            WHERE price <= 0
        ) AS invalid_price,

        COUNT(*) FILTER (
            WHERE currency_code = '643'
              AND price > 0
              AND price <= 1000
        ) AS rub_price_too_low,

        COUNT(*) FILTER (
            WHERE nearest_rate_date IS NULL
        ) AS missing_rate_date,

        COUNT(*) FILTER (
            WHERE price <= 0
              AND nearest_rate_date IS NULL
        ) AS overlap_invalid_price_and_missing_date,

        COUNT(*) FILTER (
            WHERE price <= 0
               OR (
                   currency_code = '643'
                   AND price > 0
                   AND price <= 1000
               )
               OR nearest_rate_date IS NULL
        ) AS unique_problematic_prices

    FROM public.prices
""")

with engine.connect() as connection:
    df = pd.read_sql_query(query, connection)

print(df.to_string(index=False))
