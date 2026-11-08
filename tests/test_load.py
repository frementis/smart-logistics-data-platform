import json
from decimal import Decimal

import pandas as pd

from etl.load import dataframe_to_records


def test_dataframe_to_records_preserves_decimal():
    df = pd.DataFrame({
        "id": [1],
        "price_rub": [Decimal("8567.63")],
    })

    records = dataframe_to_records(df)

    assert records[0]["price_rub"] == Decimal("8567.63")
    assert isinstance(records[0]["price_rub"], Decimal)


def test_dataframe_to_records_converts_nan_to_none():
    df = pd.DataFrame({
        "id": [1, 2],
        "value": [100.0, float("nan")],
    })

    records = dataframe_to_records(df)

    assert records[0]["value"] == 100.0
    assert records[1]["value"] is None


def test_dataframe_to_records_converts_nat_to_none():
    df = pd.DataFrame({
        "id": [1],
        "loading_date": [pd.NaT],
    })

    records = dataframe_to_records(df)

    assert records[0]["loading_date"] is None


def test_quarantine_json_serialization():
    source_record = {
        "id": 100,
        "price": Decimal("8567.63"),
        "currency_code": "643",
    }

    serialized = json.dumps(
        source_record,
        ensure_ascii=False,
        default=str,
        allow_nan=False,
    )

    restored = json.loads(serialized)

    assert restored["id"] == 100
    assert restored["price"] == "8567.63"
    assert restored["currency_code"] == "643"



from etl.load import (
    SOURCE_COLUMNS,
    load_valid_prices,
    load_quarantined_prices,
)


class FakeConnection:
    """Имитирует SQLAlchemy Connection и сохраняет вызовы execute."""

    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append({
            "query": str(query),
            "params": params,
        })


def test_load_valid_prices_builds_upsert():
    connection = FakeConnection()

    row = {column: None for column in SOURCE_COLUMNS}
    row.update({
        "id": 900001,
        "price_rub": Decimal("8567.63"),
        "core_weight_category": "FTL",
        "core_volume_category": "FTL",
    })

    df = pd.DataFrame([row])

    loaded_count = load_valid_prices(
        connection,
        df,
        batch_id=1,
    )

    assert loaded_count == 1
    assert len(connection.calls) == 2

    insert_call = connection.calls[0]

    assert "INSERT INTO core.prices" in insert_call["query"]
    assert "ON CONFLICT (id) DO UPDATE" in insert_call["query"]
    assert insert_call["params"][0]["price_rub"] == Decimal("8567.63")

    delete_call = connection.calls[1]

    assert "DELETE FROM core.dq_quarantine_prices" in delete_call["query"]
    assert delete_call["params"]["ids"] == [900001]


def test_load_quarantined_prices_builds_upsert():
    connection = FakeConnection()

    df = pd.DataFrame([{
        "id": 900002,
        "price": Decimal("500"),
        "currency_code": "643",
        "reason_code": "RUB_PRICE_TOO_LOW",
        "exchange_rate": 1.0,
        "loading_city_exists": True,
        "unloading_city_exists": True,
        "price_rub": Decimal("500"),
        "core_weight_category": "FTL",
        "core_volume_category": "FTL",
        "is_valid": False,
    }])

    quarantined_count = load_quarantined_prices(
        connection,
        df,
        batch_id=2,
    )

    assert quarantined_count == 1
    assert len(connection.calls) == 2

    insert_call = connection.calls[0]

    assert "INSERT INTO core.dq_quarantine_prices" in insert_call["query"]
    assert "ON CONFLICT (price_id) DO UPDATE" in insert_call["query"]

    record = insert_call["params"][0]

    assert record["price_id"] == 900002
    assert record["reason_code"] == "RUB_PRICE_TOO_LOW"

    source_record = json.loads(record["source_record"])

    assert source_record["price"] == "500"
    assert "exchange_rate" not in source_record
    assert "is_valid" not in source_record

    delete_call = connection.calls[1]

    assert "DELETE FROM core.prices" in delete_call["query"]
    assert delete_call["params"]["ids"] == [900002]


def test_empty_valid_dataframe_does_not_execute_sql():
    connection = FakeConnection()

    result = load_valid_prices(
        connection,
        pd.DataFrame(),
        batch_id=1,
    )

    assert result == 0
    assert connection.calls == []


def test_empty_quarantine_dataframe_does_not_execute_sql():
    connection = FakeConnection()

    result = load_quarantined_prices(
        connection,
        pd.DataFrame(),
        batch_id=1,
    )

    assert result == 0
    assert connection.calls == []