
import pandas as pd
from sqlalchemy import text

from etl.db import engine


queries = {
    "Справочник городов": """
        SELECT
            COUNT(*) AS rows_count,
            COUNT(DISTINCT gc_id) AS unique_gcids,
            COUNT(*) - COUNT(DISTINCT gc_id) AS duplicate_rows
        FROM public.cities
    """,

    "Дублирующиеся gc_id": """
        SELECT
            gc_id,
            COUNT(*) AS rows_count,
            STRING_AGG(id::text, ', ' ORDER BY id) AS city_ids,
            STRING_AGG(
                COALESCE(full_name_gc, name, 'Без названия'),
                ' | ' ORDER BY id
            ) AS city_names
        FROM public.cities
        GROUP BY gc_id
        HAVING COUNT(*) > 1
        ORDER BY rows_count DESC, gc_id
        LIMIT 20
    """,

    "Перевозки с отсутствующими городами": """
        SELECT
            COUNT(*) AS total_prices,

            COUNT(*) FILTER (
                WHERE lc.gc_id IS NULL
            ) AS missing_loading_city,

            COUNT(*) FILTER (
                WHERE uc.gc_id IS NULL
            ) AS missing_unloading_city,

            COUNT(*) FILTER (
                WHERE lc.gc_id IS NULL
                   OR uc.gc_id IS NULL
            ) AS prices_with_missing_city

        FROM public.prices p

        LEFT JOIN (
            SELECT DISTINCT gc_id
            FROM public.cities
        ) lc
            ON lc.gc_id = p.loading_city_gcid

        LEFT JOIN (
            SELECT DISTINCT gc_id
            FROM public.cities
        ) uc
            ON uc.gc_id = p.unloading_city_gcid
    """
}


with engine.connect() as connection:
    for title, sql in queries.items():
        print(f"\n{'=' * 15} {title} {'=' * 15}")

        df = pd.read_sql_query(text(sql), connection)

        if df.empty:
            print("Записей нет.")
        else:
            print(df.to_string(index=False))
