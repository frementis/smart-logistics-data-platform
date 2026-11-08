import pandas as pd
import pytest

from decimal import Decimal
from etl.quality import transform_prices


def make_row(**overrides):
    """Создаёт одну корректную запись с возможностью изменить поля."""
    row = {
        "price": 10000.0,
        "exchange_rate": 1.0,
        "currency_code": "643",
        "distance": 1000.0,
        "total_weight": 10.0,
        "total_volume": 50.0,
        "loading_city_exists": True,
        "unloading_city_exists": True,
        "nearest_rate_date": "2026-10-24",
    }
    row.update(overrides)
    return row


def test_price_conversion_to_rubles():
    df = pd.DataFrame([
        make_row(price=100.50, exchange_rate=85.25, currency_code="840")
    ])

    result = transform_prices(df)

    assert result.loc[0, "price_rub"] == Decimal("8567.63")


@pytest.mark.parametrize(
    "weight, expected",
    [
        (30.0, "G20T"),
        (29.9, "FTL"),
        (10.0, "FTL"),
        (9.9, "10T"),
        (5.0, "10T"),
        (4.9, "5T"),
        (2.5, "5T"),
        (2.4, "L5T"),
        (0.5, "L5T"),
        (0.4, "OTH"),
        (0.0, "OTH"),
    ],
)
def test_weight_categories(weight, expected):
    df = pd.DataFrame([make_row(total_weight=weight)])

    result = transform_prices(df)

    assert result.loc[0, "core_weight_category"] == expected


@pytest.mark.parametrize(
    "volume, expected",
    [
        (0.0, "OTH"),
        (0.1, "FTL"),
        (120.0, "FTL"),
        (120.1, "OTH"),
    ],
)
def test_volume_categories(volume, expected):
    df = pd.DataFrame([make_row(total_volume=volume)])

    result = transform_prices(df)

    assert result.loc[0, "core_volume_category"] == expected


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"price": 0}, "INVALID_PRICE"),
        ({"price": -100}, "INVALID_PRICE"),
        ({"price": 500, "currency_code": "643"}, "RUB_PRICE_TOO_LOW"),
        ({"distance": 0}, "INVALID_DISTANCE"),
        ({"total_weight": -1}, "INVALID_WEIGHT"),
        ({"total_volume": -1}, "INVALID_VOLUME"),
        ({"loading_city_exists": False}, "CITY_NOT_FOUND"),
        ({"unloading_city_exists": False}, "CITY_NOT_FOUND"),
        ({"nearest_rate_date": None}, "MISSING_RATE_DATE"),
        ({"exchange_rate": None}, "MISSING_EXACT_RATE"),
    ],
)
def test_quarantine_reasons(overrides, expected_reason):
    df = pd.DataFrame([make_row(**overrides)])

    result = transform_prices(df)

    assert result.loc[0, "reason_code"] == expected_reason
    assert result.loc[0, "is_valid"] == False


def test_first_quarantine_reason_has_priority():
    df = pd.DataFrame([
        make_row(price=0, distance=0)
    ])

    result = transform_prices(df)

    # INVALID_PRICE проверяется раньше INVALID_DISTANCE.
    assert result.loc[0, "reason_code"] == "INVALID_PRICE"


def test_valid_record_has_no_quarantine_reason():
    df = pd.DataFrame([make_row()])

    result = transform_prices(df)

    assert pd.isna(result.loc[0, "reason_code"])
    assert result.loc[0, "is_valid"] == True


def test_source_dataframe_is_not_modified():
    df = pd.DataFrame([make_row()])
    original = df.copy(deep=True)

    transform_prices(df)

    pd.testing.assert_frame_equal(df, original)