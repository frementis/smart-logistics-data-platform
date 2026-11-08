from etl.db import engine
from etl.batches import start_batch, finish_batch
from etl.extract import extract_prices_in_batches
from etl.quality import transform_prices
from etl.load import load_valid_prices, load_quarantined_prices


# Берём только первый пакет из источника
batch = next(extract_prices_in_batches(batch_size=100))

# Проверяем качество данных
transformed = transform_prices(batch)

valid = transformed[transformed["is_valid"]]
quarantined = transformed[~transformed["is_valid"]]

print(f"Получено записей: {len(batch)}")
print(f"Валидных: {len(valid)}")
print(f"В карантине: {len(quarantined)}")


# Загружаем данные в рамках одной транзакции
with engine.begin() as connection:
    batch_id = start_batch(connection, source_count=len(batch))

    loaded_count = load_valid_prices(
        connection, valid, batch_id
    )

    quarantined_count = load_quarantined_prices(
        connection, quarantined, batch_id
    )

    finish_batch(
        connection,
        batch_id,
        loaded_count,
        quarantined_count,
    )

print(f"\nТестовая загрузка завершена. batch_id: {batch_id}")