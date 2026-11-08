
import pandas as pd
from sqlalchemy import text

from etl.db import engine


query = text("""
    WITH dq_issues AS (
        SELECT
            p.id AS price_id,
            issue.reason_code
        FROM public.prices p

        LEFT JOIN public.exchange_rates er
            ON er.num_code = p.currency_code
            AND er.setting_date = p.nearest_rate_date

        CROSS JOIN LATERAL (
            SELECT unnest(ARRAY[
                CASE
                    WHEN p.price <= 0
                    THEN 'INVALID_PRICE'
                END,

                CASE
                    WHEN p.currency_code = '643'
                         AND p.price > 0
                         AND p.price <= 1000
                    THEN 'RUB_PRICE_TOO_LOW'
                END,

                CASE
                    WHEN p.distance <= 0
                    THEN 'INVALID_DISTANCE'
                END,

                CASE
                    WHEN p.total_weight < 0
                    THEN 'INVALID_WEIGHT'
                END,

                CASE
                    WHEN p.total_volume < 0
                    THEN 'INVALID_VOLUME'
                END,

                CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM public.cities c
                        WHERE c.gc_id = p.loading_city_gcid
                    )
                    OR NOT EXISTS (
                        SELECT 1
                        FROM public.cities c
                        WHERE c.gc_id = p.unloading_city_gcid
                    )
                    THEN 'CITY_NOT_FOUND'
                END,

                CASE
                    WHEN p.nearest_rate_date IS NULL
                    THEN 'MISSING_RATE_DATE'
                END,

                CASE
                    WHEN p.nearest_rate_date IS NOT NULL
                         AND er.num_code IS NULL
                    THEN 'MISSING_EXACT_RATE'
                END
            ]) AS reason_code
        ) issue

        WHERE issue.reason_code IS NOT NULL
    )

    SELECT
        reason_code,
        COUNT(*) AS violations_count,
        COUNT(DISTINCT price_id) AS affected_prices
    FROM dq_issues
    GROUP BY reason_code
    ORDER BY reason_code
""")

with engine.connect() as connection:
    df = pd.read_sql_query(query, connection)

print("Результаты проверки качества данных:")

if df.empty:
    print("Нарушений не обнаружено.")
else:
    print(df.to_string(index=False))

    print(
        "\nВсего нарушений:",
        df["violations_count"].sum()
    )

    print(
        "Уникальных записей с нарушениями:",
        df["affected_prices"].sum()
        if df["reason_code"].is_unique
        else "См. отдельный подсчёт ниже"
    )
