
import pandas as pd
from sqlalchemy import text

from etl.db import engine


query = text("""
    SELECT num_code, setting_date, value
    FROM (
        SELECT
            num_code,
            setting_date,
            value,
            ROW_NUMBER() OVER (
                PARTITION BY num_code
                ORDER BY setting_date
            ) AS rn
        FROM public.exchange_rates
        WHERE num_code IN ('840', '978')
    ) rates
    WHERE rn <= 5
    ORDER BY num_code, setting_date
""")

with engine.connect() as connection:
    df = pd.read_sql_query(query, connection)

print("Примеры курсов валют:")
print(df.to_string(index=False))
