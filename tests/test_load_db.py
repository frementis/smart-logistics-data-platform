import pandas as pd
from sqlalchemy import text

from etl.db import engine
from etl.load import (
    CORE_COLUMNS,
    SOURCE_COLUMNS,
    load_valid_prices,
    load_quarantined_prices,
)


def test_loaders_are_idempotent_and_move_records_between_tables():
    test_id = -900001

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            # Берём существующую запись как шаблон,
            # чтобы заполнить все обязательные поля.
            sample = pd.read_sql_query(
                text("""
                    SELECT *
                    FROM core.prices
                    LIMIT 1
                """),
                connection,
            )

            assert not sample.empty, "В core.prices нет записей для теста"

            sample = sample[CORE_COLUMNS].copy()
            batch_id = int(sample.loc[0, "batch_id"])
            sample.loc[0, "id"] = test_id

            # Проверяем, что тестовый ID ещё не занят.
            existing = connection.execute(
                text("""
                    SELECT
                        EXISTS (
                            SELECT 1 FROM core.prices WHERE id = :id
                        )
                        OR EXISTS (
                            SELECT 1 FROM core.dq_quarantine_prices
                            WHERE price_id = :id
                        )
                """),
                {"id": test_id},
            ).scalar()

            assert not existing, f"Тестовый ID {test_id} уже существует"

            # 1. Дважды загружаем валидную запись.
            assert load_valid_prices(connection, sample, batch_id) == 1
            assert load_valid_prices(connection, sample, batch_id) == 1

            core_count = connection.execute(
                text("SELECT COUNT(*) FROM core.prices WHERE id = :id"),
                {"id": test_id},
            ).scalar()

            assert core_count == 1

            # 2. Переносим запись в карантин.
            quarantine_df = sample[
                SOURCE_COLUMNS + [
                    "price_rub",
                    "core_weight_category",
                    "core_volume_category",
                ]
            ].copy()

            quarantine_df["reason_code"] = "INVALID_PRICE"

            assert load_quarantined_prices(
                connection, quarantine_df, batch_id
            ) == 1

            # Повторная загрузка не должна создавать дубликат.
            assert load_quarantined_prices(
                connection, quarantine_df, batch_id
            ) == 1

            quarantine_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM core.dq_quarantine_prices
                    WHERE price_id = :id
                """),
                {"id": test_id},
            ).scalar()

            core_count = connection.execute(
                text("SELECT COUNT(*) FROM core.prices WHERE id = :id"),
                {"id": test_id},
            ).scalar()

            assert quarantine_count == 1
            assert core_count == 0

            # 3. Возвращаем запись в Core.
            assert load_valid_prices(connection, sample, batch_id) == 1

            core_count = connection.execute(
                text("SELECT COUNT(*) FROM core.prices WHERE id = :id"),
                {"id": test_id},
            ).scalar()

            quarantine_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM core.dq_quarantine_prices
                    WHERE price_id = :id
                """),
                {"id": test_id},
            ).scalar()

            assert core_count == 1
            assert quarantine_count == 0

        finally:
            # Откатываем всю транзакцию.
            # Тестовая запись не останется в БД.
            transaction.rollback()