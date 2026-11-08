
import pandas as pd
from sqlalchemy import text

from etl.db import engine


SOURCE_QUERY = text("""
    SELECT
        p.*,

        er.value AS exchange_rate,

        EXISTS (
            SELECT 1
            FROM public.cities c
            WHERE c.gc_id = p.loading_city_gcid
        ) AS loading_city_exists,

        EXISTS (
            SELECT 1
            FROM public.cities c
            WHERE c.gc_id = p.unloading_city_gcid
        ) AS unloading_city_exists

    FROM public.prices p

    LEFT JOIN public.exchange_rates er
        ON er.num_code = p.currency_code
        AND er.setting_date = p.nearest_rate_date

    ORDER BY p.id
""")


def get_source_count() -> int:
    query = text("SELECT COUNT(*) FROM public.prices")

    with engine.connect() as connection:
        return connection.execute(query).scalar_one()


def extract_prices_in_batches(batch_size: int = 10_000):
    """
    Читает исходные перевозки пакетами.
    Каждый вызов генератора возвращает DataFrame с очередной порцией данных.
    """

    with engine.connect() as connection:
        batches = pd.read_sql_query(
            SOURCE_QUERY,
            connection,
            chunksize=batch_size
        )

        yield from batches


if __name__ == "__main__":
    total_count = get_source_count()

    print(f"Всего записей в источнике: {total_count}")

    extracted_count = 0

    for batch_number, batch in enumerate(
        extract_prices_in_batches(),
        start=1
    ):
        extracted_count += len(batch)

        print(
            f"Пакет {batch_number}: "
            f"{len(batch)} записей, "
            f"всего прочитано: {extracted_count}"
        )

    print(f"\nВсего прочитано: {extracted_count}")
