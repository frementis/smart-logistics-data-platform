from etl.transform import extract_prices_with_rates
from etl.quality import transform_prices


df = extract_prices_with_rates(limit=10)
df = transform_prices(df)

columns = [
    "id",
    "price",
    "currency_code",
    "exchange_rate",
    "price_rub",
    "total_weight",
    "core_weight_category",
    "total_volume",
    "core_volume_category",
    "is_valid",
    "reason_code",
]

print(df[columns].to_string(index=False))
