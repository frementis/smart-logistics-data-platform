
import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text


# Исходные поля public.prices.
SOURCE_COLUMNS = [
    "id",
    "created_at",
    "updated_at",
    "subscriber_id",
    "organization_id",
    "loading_date",
    "loading_city_gcid",
    "unloading_city_gcid",
    "distance",
    "total_weight",
    "total_volume",
    "body_type",
    "price",
    "currency_code",
    "complex",
    "price_type",
    "item_id",
    "is_fact",
    "nearest_rate_date",
    "meta_item_id",
    "end_loading_date",
    "source",
    "external_item_uuid",
    "outlier_mark",
    "weight_category",
    "volume_category",
    "price_group_id",
]

CORE_COLUMNS = SOURCE_COLUMNS + [
    "price_rub",
    "core_weight_category",
    "core_volume_category",
    "processed_at",
    "batch_id",
]


def dataframe_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Преобразует DataFrame в список словарей
    и заменяет NaN/NaT на None для PostgreSQL.
    """
    clean_df = df.astype(object).where(pd.notna(df), None)
    return clean_df.to_dict(orient="records")


def load_valid_prices(
    connection,
    df: pd.DataFrame,
    batch_id: int,
) -> int:
    """
    Загружает валидные перевозки в core.prices.
    При повторной загрузке обновляет существующие записи.
    """

    if df.empty:
        return 0

    records_df = df[SOURCE_COLUMNS + [
        "price_rub",
        "core_weight_category",
        "core_volume_category",
    ]].copy()

    records_df["processed_at"] = datetime.now(timezone.utc)
    records_df["batch_id"] = batch_id

    records = dataframe_to_records(records_df)

    columns_sql = ", ".join(CORE_COLUMNS)
    values_sql = ", ".join(
        f":{column}" for column in CORE_COLUMNS
    )

    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in CORE_COLUMNS
        if column != "id"
    )

    query = text(f"""
        INSERT INTO core.prices ({columns_sql})
        VALUES ({values_sql})
        ON CONFLICT (id) DO UPDATE SET
            {update_sql}
    """)

    connection.execute(query, records)

    # Если запись раньше находилась в карантине,
    # а теперь стала валидной, удаляем её оттуда.
    ids = [record["id"] for record in records]

    connection.execute(
        text("""
            DELETE FROM core.dq_quarantine_prices
            WHERE price_id = ANY(CAST(:ids AS bigint[]))
        """),
        {"ids": ids},
    )

    return len(records)


def load_quarantined_prices(
    connection,
    df: pd.DataFrame,
    batch_id: int,
) -> int:
    """
    Загружает невалидные перевозки в карантин.
    Исходная запись сохраняется целиком в JSONB.
    """

    if df.empty:
        return 0

    quarantined_at = datetime.now(timezone.utc).replace(tzinfo=None)

    records = []

    for row in dataframe_to_records(df):
        source_record = {
            key: value
            for key, value in row.items()
            if key not in {
                "exchange_rate",
                "loading_city_exists",
                "unloading_city_exists",
                "price_rub",
                "core_weight_category",
                "core_volume_category",
                "reason_code",
                "is_valid",
            }
        }

        records.append({
            "price_id": int(row["id"]),
            "batch_id": batch_id,
            "reason_code": str(row["reason_code"]),
            "reason_detail": str(row["reason_code"]),
            "source_record": json.dumps(
                source_record,
                ensure_ascii=False,
                default=str,
                allow_nan=False,

            ),
            "quarantined_at": quarantined_at,
        })

    query = text("""
        INSERT INTO core.dq_quarantine_prices (
            price_id,
            batch_id,
            reason_code,
            reason_detail,
            source_record,
            quarantined_at
        )
        VALUES (
            :price_id,
            :batch_id,
            :reason_code,
            :reason_detail,
            CAST(:source_record AS jsonb),
            :quarantined_at
        )
        ON CONFLICT (price_id) DO UPDATE SET
            batch_id = EXCLUDED.batch_id,
            reason_code = EXCLUDED.reason_code,
            reason_detail = EXCLUDED.reason_detail,
            source_record = EXCLUDED.source_record,
            quarantined_at = EXCLUDED.quarantined_at
    """)

    connection.execute(query, records)

    # Если запись раньше была валидной,
    # а теперь оказалась невалидной, удаляем её из Core.
    ids = [record["price_id"] for record in records]

    connection.execute(
        text("""
            DELETE FROM core.prices
            WHERE id = ANY(CAST(:ids AS bigint[]))
        """),
        {"ids": ids},
    )

    return len(records)
