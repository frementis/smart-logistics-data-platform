
import pandas as pd
from sqlalchemy import text

from etl.db import engine


query = text("""
    SELECT
        p.currency_code,
        COUNT(*) AS prices_count,
        COUNT(*) FILTER (
            WHERE p.nearest_rate_date IS NULL
        ) AS missing_rate_date,
        COUNT(*) FILTER (
            WHERE p.nearest_rate_date IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM public.exchange_rates er
                  WHERE er.num_code = p.currency_code
                    AND er.setting_date = p.nearest_rate_date
              )
        ) AS missing_exact_rate
    FROM public.prices p
    GROUP BY p.currency_code
    ORDER BY p.currency_code
""")

with engine.connect() as connection:
    df = pd.read_sql_query(query, connection)

print("Покрытие курсов валют:")
print(df.to_string(index=False))
