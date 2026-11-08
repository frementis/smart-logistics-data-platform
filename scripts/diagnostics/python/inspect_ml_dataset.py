
from etl.ml_dataset import extract_ml_dataset

df = extract_ml_dataset()

print("Размер датасета:", df.shape)

print("\nРаспределение выборок:")
print(df["dataset_split"].value_counts())

print("\nПроверка целевой переменной:")
print(df.groupby("dataset_split")["target_price_rub"].agg(
    ["count", "min", "max"]
))

print("\nПервые 5 строк:")
print(df.head().to_string(index=False))

print("\nПропуски:")
print(df.isna().sum())
