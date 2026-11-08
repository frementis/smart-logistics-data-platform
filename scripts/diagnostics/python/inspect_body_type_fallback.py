
import pandas as pd
from sqlalchemy import text
from etl.db import engine

queries = {
    "Заполнение prices.body_type у перевозок без связей": """
        SELECT
            COUNT(*) AS prices_without_links,
            COUNT(*) FILTER (
                WHERE p.body_type IS NULL
            ) AS body_type_is_null,
            COUNT(*) FILTER (
                WHERE p.body_type IS NOT NULL
                  AND bt.id IS NULL
            ) AS body_type_not_found_in_dictionary,
            COUNT(*) FILTER (
                WHERE bt.id IS NOT NULL
            ) AS body_type_found_in_dictionary
        FROM public.prices p
        LEFT JOIN public.body_types bt
            ON bt.id = p.body_type
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.price_body_types pbt
            WHERE pbt.price_id = p.id
        )
    """,

    "Распределение запасных типов кузова": """
        SELECT
            p.body_type,
            bt.name,
            bt.std_id,
            COUNT(*) AS prices_count
        FROM public.prices p
        LEFT JOIN public.body_types bt
            ON bt.id = p.body_type
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.price_body_types pbt
            WHERE pbt.price_id = p.id
        )
        GROUP BY p.body_type, bt.name, bt.std_id
        ORDER BY prices_count DESC
    """
}

with engine.connect() as connection:
    for title, sql in queries.items():
        print(f"\n{'=' * 15} {title} {'=' * 15}")
        df = pd.read_sql_query(text(sql), connection)
        print(df.to_string(index=False))
