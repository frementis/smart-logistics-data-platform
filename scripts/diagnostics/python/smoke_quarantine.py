from etl.db import engine
from etl.batches import start_batch, finish_batch
from etl.extract import extract_prices_in_batches
from etl.quality import transform_prices
from etl.load import load_quarantined_prices

invalid_record = None

for batch in extract_prices_in_batches(batch_size=10_000):
    transformed = transform_prices(batch)
    invalid = transformed[~transformed["is_valid"]]

    if not invalid.empty:
        invalid_record = invalid.iloc[[0]]
        break

if invalid_record is None:
    raise RuntimeError("В исходных данных не найдены невалидные записи")

print("Найдена невалидная запись:")
print(f"ID: {invalid_record.iloc[0]['id']}")
print(f"Причина: {invalid_record.iloc[0]['reason_code']}")

with engine.begin() as connection:
    batch_id = start_batch(connection, source_count=1)

    quarantined_count = load_quarantined_prices(
        connection,
        invalid_record,
        batch_id,
    )

    finish_batch(
        connection,
        batch_id,
        loaded_count=0,
        quarantined_count=quarantined_count,
    )

print(f"\nТест карантина завершён. batch_id: {batch_id}")