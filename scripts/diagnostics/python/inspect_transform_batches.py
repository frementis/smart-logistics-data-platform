from collections import Counter

from etl.extract import extract_prices_in_batches, get_source_count
from etl.quality import transform_prices


total_count = get_source_count()

valid_count = 0
quarantined_count = 0

reason_counts = Counter()
weight_category_counts = Counter()
volume_category_counts = Counter()

processed_count = 0

for batch_number, batch in enumerate(
    extract_prices_in_batches(batch_size=10_000),
    start=1,
):
    transformed = transform_prices(batch)

    valid_count += int(transformed["is_valid"].sum())
    quarantined_count += int((~transformed["is_valid"]).sum())

    reason_counts.update(
        transformed["reason_code"].dropna().tolist()
    )

    weight_category_counts.update(
        transformed["core_weight_category"].value_counts().to_dict()
    )

    volume_category_counts.update(
        transformed["core_volume_category"].value_counts().to_dict()
    )

    processed_count += len(transformed)

    print(
        f"Пакет {batch_number}: "
        f"обработано {len(transformed)}, "
        f"всего {processed_count}"
    )


print("\n=============== Итог Transform ===============")
print(f"Источник:             {total_count}")
print(f"Обработано:           {processed_count}")
print(f"Валидных:             {valid_count}")
print(f"В карантин:           {quarantined_count}")

print("\n=============== Причины карантина ===============")
for reason, count in reason_counts.most_common():
    print(f"{reason}: {count}")

print("\n=============== Категории веса ===============")
for category, count in weight_category_counts.most_common():
    print(f"{category}: {count}")

print("\n=============== Категории объёма ===============")
for category, count in volume_category_counts.most_common():
    print(f"{category}: {count}")

print("\nПроверка общего количества:")
print(f"{valid_count} + {quarantined_count} = "
      f"{valid_count + quarantined_count}")
