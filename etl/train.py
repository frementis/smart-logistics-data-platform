
from pathlib import Path

import numpy as np
from catboost import CatBoostRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

from etl.ml_dataset import extract_ml_dataset


CATEGORICAL_FEATURES = [
    "loading_city",
    "loading_region",
    "unloading_city",
    "unloading_region",
    "body_group",
    "weight_category",
    "volume_category",
]

NUMERIC_FEATURES = [
    "loading_longitude",
    "loading_latitude",
    "unloading_longitude",
    "unloading_latitude",
    "distance",
    "total_weight",
    "total_volume",
    "loading_year",
    "loading_month",
    "loading_weekday",
    "loading_day_of_year",
    "month_sin",
    "month_cos",
    "weekday_sin",
    "weekday_cos",
    "day_of_year_sin",
    "day_of_year_cos",
]

FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def train_model():
    # Получаем подготовленный датасет
    df = extract_ml_dataset()

    # Разделяем выборки по заранее заданным временным границам
    train_df = df[df["dataset_split"] == "train"].copy()
    test_df = df[df["dataset_split"] == "test"].copy()

    X_train = train_df[FEATURES].copy()
    y_train = train_df["target_price_rub"]

    X_test = test_df[FEATURES].copy()
    y_test = test_df["target_price_rub"]

    # CatBoost ожидает категориальные признаки в строковом формате
    for column in CATEGORICAL_FEATURES:
        X_train[column] = X_train[column].astype(str)
        X_test[column] = X_test[column].astype(str)

    print(f"Train records: {len(X_train)}")
    print(f"Test records: {len(X_test)}")
    print(f"Features: {len(FEATURES)}")

    # Создаём и обучаем модель
    model = CatBoostRegressor(
        iterations=1000,
        depth=8,
        learning_rate=0.05,
        loss_function="RMSE",
        eval_metric="RMSE",
        random_seed=42,
        verbose=100,
        allow_writing_files=False,
        thread_count=-1,
    )

    model.fit(
        X_train,
        y_train,
        cat_features=CATEGORICAL_FEATURES,
    )

    # Получаем предсказания на тестовой выборке
    predictions = model.predict(X_test)

    # Рассчитываем метрики
    metrics = {
        "R2": r2_score(y_test, predictions),
        "MAPE (%)": mean_absolute_percentage_error(
            y_test, predictions
        ) * 100,
        "RMSE": np.sqrt(mean_squared_error(y_test, predictions)),
        "MAE": mean_absolute_error(y_test, predictions),
    }

    print("\nМетрики на тестовой выборке:")
    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")

    # Сохраняем обученную модель
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / "catboost_price_model.cbm"
    model.save_model(str(model_path))

    print(f"\nМодель сохранена: {model_path}")

    return model, metrics


if __name__ == "__main__":
    train_model()
