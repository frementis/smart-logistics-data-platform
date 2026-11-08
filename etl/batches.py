from sqlalchemy import text


def start_batch(connection, source_count: int) -> int:
    query = text("""
        INSERT INTO core.etl_batches (source_count)
        VALUES (:source_count)
        RETURNING batch_id
    """)

    batch_id = connection.execute(
        query,
        {"source_count": source_count},
    ).scalar_one()

    return batch_id


def finish_batch(
    connection,
    batch_id: int,
    loaded_count: int,
    quarantined_count: int,
):
    query = text("""
        UPDATE core.etl_batches
        SET
            finished_at = CURRENT_TIMESTAMP,
            status = 'SUCCESS',
            loaded_count = :loaded_count,
            quarantined_count = :quarantined_count
        WHERE batch_id = :batch_id
    """)

    connection.execute(
        query,
        {
            "batch_id": batch_id,
            "loaded_count": loaded_count,
            "quarantined_count": quarantined_count,
        },
    )


def fail_batch(connection, batch_id: int, error_message: str):
    query = text("""
        UPDATE core.etl_batches
        SET
            finished_at = CURRENT_TIMESTAMP,
            status = 'FAILED',
            error_message = :error_message
        WHERE batch_id = :batch_id
    """)

    connection.execute(
        query,
        {
            "batch_id": batch_id,
            "error_message": error_message[:5000],
        },
    )