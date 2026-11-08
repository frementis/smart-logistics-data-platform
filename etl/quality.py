from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd


def transform_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Рассчитывает рублёвую стоимость и категории перевозок."""

    df = df.copy()

    # Пересчёт стоимости в рубли.
    def calculate_price_rub(price, exchange_rate):
        if pd.isna(price) or pd.isna(exchange_rate):
            return None

        result = Decimal(str(price)) * Decimal(str(exchange_rate))

        return result.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )


    df["price_rub"] = [
        calculate_price_rub(price, rate)
        for price, rate in zip(df["price"], df["exchange_rate"])
    ]

    # Вес сначала округляем до 0.1 тонны.
    weight = df["total_weight"].round(1)

    df["core_weight_category"] = np.select(
        [
            weight >= 30,
            (weight >= 10) & (weight < 30),
            (weight >= 5) & (weight < 10),
            (weight >= 2.5) & (weight < 5),
            (weight >= 0.5) & (weight < 2.5),
        ],
        ["G20T", "FTL", "10T", "5T", "L5T"],
        default="OTH",
    )

    # Объём: FTL только при 0 < volume <= 120.
    df["core_volume_category"] = np.where(
        (df["total_volume"] > 0)
        & (df["total_volume"] <= 120),
        "FTL",
        "OTH",
    )

    # Последовательно определяем первую причину отклонения.
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
        mask = df["reason_code"].isna() & condition.fillna(False)
        df.loc[mask, "reason_code"] = reason

    df["is_valid"] = df["reason_code"].isna()

    return df
