from sqlalchemy import text


REBUILD_BODY_GROUPS_QUERY = text("""
    WITH linked_types AS (
        -- Основной источник: все типы кузовов,
        -- связанные с перевозкой через price_body_types.
        SELECT
            pbt.price_id,
            bt.id AS body_type_id,
            bt.std_id
        FROM public.price_body_types pbt
        JOIN public.body_types bt
            ON bt.id = pbt.body_type_id
        JOIN core.prices cp
            ON cp.id = pbt.price_id
    ),

    fallback_types AS (
        -- Резервный источник: prices.body_type.
        -- Используем его только если у перевозки нет связей.
        SELECT
            cp.id AS price_id,
            bt.id AS body_type_id,
            bt.std_id
        FROM core.prices cp
        JOIN public.body_types bt
            ON bt.id = cp.body_type
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.price_body_types pbt
            WHERE pbt.price_id = cp.id
        )
    ),

    all_types AS (
        SELECT * FROM linked_types
        UNION ALL
        SELECT * FROM fallback_types
    ),

    standardized_groups AS (
        SELECT DISTINCT
            price_id,
            CASE
                WHEN body_type_id IS NULL THEN 'Не указан'
                WHEN std_id = 56 THEN 'Тент'
                WHEN std_id = 4 THEN 'Рефрижератор'
                WHEN std_id = 2 THEN 'Изотерм'
                WHEN std_id = 15 THEN 'Борт'
                ELSE 'Прочие'
            END AS body_group
        FROM all_types

        UNION

        -- Если нет ни связей, ни резервного типа,
        -- присваиваем группу "Не указан".
        SELECT
            cp.id AS price_id,
            'Не указан' AS body_group
        FROM core.prices cp
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.price_body_types pbt
            WHERE pbt.price_id = cp.id
        )
        AND cp.body_type IS NULL
    )

    INSERT INTO core.price_body_groups (
        price_id,
        body_group
    )
    SELECT
        price_id,
        body_group
    FROM standardized_groups
    ON CONFLICT (price_id, body_group) DO NOTHING
""")


def rebuild_price_body_groups(connection) -> int:
    # Удаляем предыдущую версию групп.
    # При ошибке вся транзакция откатится.
    connection.execute(
        text("DELETE FROM core.price_body_groups")
    )

    # Заново строим связи на основании актуальных данных.
    result = connection.execute(REBUILD_BODY_GROUPS_QUERY)

    return result.rowcount