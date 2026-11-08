
import numpy as np
import pandas as pd


def transform_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Преобразует пакет исходных перевозок:
    - рассчитывает цену в рублях;
    - определяет категории веса и объёма;
    - проверяет качество данных;
    - помечает невалидные записи причиной отклонения.

    Функция не изменяет исходный DataFrame и не обращается к БД.
    """

    df = df.copy()

    # 1. Пересчёт цены в рубли.
    # Курс уже присоединён на этапе Extract по точной дате nearest_rate_date.
    df["price_rub"] = (
        df["price"] * df["exchange_rate"]
    ).round(2)

    # 2. Категория веса.
    # Сначала округляем вес до 0.1 тонны, как требует задание.
    weight = df["total_weight"].round(1)

    df["core_weight_category"] = np.select(
        [
            weight >= 30,
            (weight >= 10) & (weight < 30),
            (weight >= 5) & (weight < 10),
            (weight >= 2.5) & (weight < 5),
            (weight >= 0.5) & (weight < 2.5),
        ],
        [
            "G20T",
            "FTL",
            "10T",
            "5T",
            "L5T",
        ],
        default="OTH",
    )

    # 3. Категория объёма.
    df["core_volume_category"] = np.where(
        (df["total_volume"] > 0)
        & (df["total_volume"] <= 120),
        "FTL",
        "OTH",
    )

    # 4. Причина отклонения.
    # Если найдено несколько нарушений, сохраняем первое по порядку.
    df["reason_code"] = pd.NA

    checks = [
        (
            df["price"] <= 0,
            "INVALID_PRICE",
        ),
        (
            (df["currency_code"] == "643")
            & (df["price"] > 0)
            & (df["price"] <= 1000),
            "RUB_PRICE_TOO_LOW",
        ),
        (
            df["distance"] <= 0,
            "INVALID_DISTANCE",
        ),
        (
            df["total_weight"] < 0,
            "INVALID_WEIGHT",
        ),
        (
            df["total_volume"] < 0,
            "INVALID_VOLUME",
        ),
        (
            ~df["loading_city_exists"]
            | ~df["unloading_city_exists"],
            "CITY_NOT_FOUND",
        ),
        (
            df["nearest_rate_date"].isna(),
            "MISSING_RATE_DATE",
        ),
        (
            df["exchange_rate"].isna(),
            "MISSING_EXACT_RATE",
        ),
    ]

    for condition, reason in checks:
        mask = (
            df["reason_code"].isna()
            & condition.fillna(False)
        )
        df.loc[mask, "reason_code"] = reason

    # 5. Итоговый признак качества.
    df["is_valid"] = df["reason_code"].isna()

    return df
