
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sqlalchemy import text

from etl.db import engine
from etl.ml_dataset import extract_ml_dataset
from etl.train import FEATURES, CATEGORICAL_FEATURES


MODEL_NAME = "catboost_price_model_v1"
MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "catboost_price_model.cbm"
)


def run_batch_inference():
    # 1. Загружаем обученную модель
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Модель не найдена: {MODEL_PATH}")

    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH))

    # 2. Получаем данные для тестирования и будущих прогнозов
    df = extract_ml_dataset()

    prediction_df = df[
        df["dataset_split"].isin(["test", "future"])
    ].copy()

    # 3. Подготавливаем признаки в том же порядке, что и при обучении
    X = prediction_df[FEATURES].copy()

    for column in CATEGORICAL_FEATURES:
        X[column] = X[column].astype(str)

    # 4. Рассчитываем прогнозы
    predictions = model.predict(X)
    predictions = np.round(predictions, 2)

    # 5. Рассчитываем ошибки только для тестовой выборки
    is_test = prediction_df["dataset_split"].eq("test")

    actual_prices = pd.to_numeric(
        prediction_df["target_price_rub"]
    )

    abs_errors = (actual_prices - predictions).abs().where(is_test)

    ape_pct = (
        abs_errors / actual_prices * 100
    ).where(is_test)

    # 6. Формируем таблицу результатов
    results = pd.DataFrame({
        "price_id": prediction_df["price_id"],
        "dataset_split": prediction_df["dataset_split"],
        "loading_date": prediction_df["loading_date"],
        "loading_city_gcid": prediction_df["loading_city_gcid"],
        "unloading_city_gcid": prediction_df["unloading_city_gcid"],
        "body_group": prediction_df["body_group"],
        "actual_price_rub": actual_prices.where(is_test),
        "predicted_price_rub": predictions,
        "abs_error_rub": abs_errors.round(2),
        "ape_pct": ape_pct.round(4),
        "model_name": MODEL_NAME,
    })

    # 7. Сохраняем результаты одной транзакцией
    with engine.begin() as connection:
        connection.execute(text("""
            DELETE FROM mart.ml_predictions
            WHERE dataset_split IN ('test', 'future')
        """))

        results.to_sql(
            name="ml_predictions",
            schema="mart",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )

    # 8. Выводим статистику загрузки
    print("Batch inference завершён.")
    print(f"Всего прогнозов: {len(results)}")
    print(f"Test: {int(is_test.sum())}")
    print(f"Future: {int((~is_test).sum())}")
    print(f"Модель: {MODEL_NAME}")

    print("\nСредние ошибки на test:")
    print(f"MAE: {abs_errors[is_test].mean():.2f} RUB")
    print(f"MAPE: {ape_pct[is_test].mean():.2f}%")


if __name__ == "__main__":
    run_batch_inference()
