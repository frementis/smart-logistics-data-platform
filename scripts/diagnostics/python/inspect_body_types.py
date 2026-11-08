
import pandas as pd
from sqlalchemy import text
from etl.db import engine

queries = {
    "Справочник типов кузова": """
        SELECT
            id,
            name,
            "id_from_1C",
            std_id
        FROM public.body_types
        ORDER BY id
    """,

    "Количество типов кузова на перевозку": """
        WITH body_counts AS (
            SELECT
                p.id AS price_id,
                COUNT(pbt.body_type_id) AS body_types_count
            FROM public.prices p
            LEFT JOIN public.price_body_types pbt
                ON pbt.price_id = p.id
            GROUP BY p.id
        )
        SELECT
            body_types_count,
            COUNT(*) AS prices_count
        FROM body_counts
        GROUP BY body_types_count
        ORDER BY body_types_count
    """,

    "Связи с типами кузова": """
        SELECT
            COUNT(*) AS total_links,
            COUNT(*) FILTER (
                WHERE bt.id IS NULL
            ) AS missing_body_types,
            COUNT(DISTINCT pbt.price_id) AS prices_with_body_types
        FROM public.price_body_types pbt
        LEFT JOIN public.body_types bt
            ON bt.id = pbt.body_type_id
    """
}

with engine.connect() as connection:
    for title, sql in queries.items():
        print(f"\\n{'=' * 15} {title} {'=' * 15}")
        df = pd.read_sql_query(text(sql), connection)

        if df.empty:
            print("Записей нет.")
        else:
            print(df.to_string(index=False))
