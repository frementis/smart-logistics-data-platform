from etl.db import engine
from etl.extract import get_source_count, extract_prices_in_batches
from etl.quality import transform_prices
from etl.load import load_valid_prices, load_quarantined_prices
from etl.batches import start_batch, finish_batch, fail_batch


def run_etl(batch_size: int = 10_000):
    total_source_count = get_source_count()

    print(f"Записей в источнике: {total_source_count}")
    print(f"Размер пакета: {batch_size}")
    print("-" * 50)

    total_loaded = 0
    total_quarantined = 0
    total_processed = 0

    for batch_number, source_batch in enumerate(
        extract_prices_in_batches(batch_size=batch_size),
        start=1,
    ):
        batch_count = len(source_batch)

        # Создаём запись о новом ETL-пакете.
        with engine.begin() as connection:
            batch_id = start_batch(
                connection,
                source_count=batch_count,
            )

        try:
            # Проверяем данные и рассчитываем новые поля.
            transformed = transform_prices(source_batch)

            valid = transformed[transformed["is_valid"]]
            quarantined = transformed[~transformed["is_valid"]]

            # Загружаем данные одной транзакцией.
            # Если что-то пойдёт не так, изменения этого пакета откатятся.
            with engine.begin() as connection:
                loaded_count = load_valid_prices(
                    connection,
                    valid,
                    batch_id,
                )

                quarantined_count = load_quarantined_prices(
                    connection,
                    quarantined,
                    batch_id,
                )

                finish_batch(
                    connection,
                    batch_id,
                    loaded_count,
                    quarantined_count,
                )

            total_processed += batch_count
            total_loaded += loaded_count
            total_quarantined += quarantined_count

            print(
                f"Пакет {batch_number}: "
                f"обработано {batch_count}, "
                f"загружено {loaded_count}, "
                f"карантин {quarantined_count}, "
                f"всего {total_processed}"
            )

        except Exception as error:
            # Если пакет упал, сохраняем информацию об ошибке.
            with engine.begin() as connection:
                fail_batch(
                    connection,
                    batch_id,
                    str(error),
                )

            print(f"Ошибка в пакете {batch_number}: {error}")
            raise

    print("\n" + "=" * 50)
    print("ETL завершён")
    print(f"Всего в источнике: {total_source_count}")
    print(f"Обработано: {total_processed}")
    print(f"Загружено в Core: {total_loaded}")
    print(f"Отправлено в карантин: {total_quarantined}")
    print("=" * 50)

    if total_processed != total_source_count:
        raise RuntimeError(
            "Количество обработанных записей не совпадает с источником"
        )


if __name__ == "__main__":
    run_etl()