
import pandas as pd
from sqlalchemy import text
from etl.db import engine

query = """
WITH source_types AS (
    -- Основной источник: связи price_body_types
    SELECT
        pbt.price_id,
        bt.std_id
    FROM public.price_body_types pbt
    JOIN public.body_types bt
        ON bt.id = pbt.body_type_id

    UNION

    -- Запасной источник: prices.body_type,
    -- только если связей price_body_types нет
    SELECT
        p.id AS price_id,
        bt.std_id
    FROM public.prices p
    JOIN public.body_types bt
        ON bt.id = p.body_type
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.price_body_types pbt
        WHERE pbt.price_id = p.id
    )
),

standard_groups AS (
    SELECT DISTINCT
        price_id,
        CASE
            WHEN std_id = 56 THEN 'Тент'
            WHEN std_id = 4 THEN 'Рефрижератор'
            WHEN std_id = 2 THEN 'Изотерм'
            WHEN std_id = 15 THEN 'Борт'
            ELSE 'Прочие'
        END AS body_group
    FROM source_types
),

price_group_counts AS (
    SELECT
        p.id AS price_id,
        COUNT(sg.body_group) AS groups_count
    FROM public.prices p
    LEFT JOIN standard_groups sg
        ON sg.price_id = p.id
    GROUP BY p.id
)

SELECT
    groups_count,
    COUNT(*) AS prices_count
FROM price_group_counts
GROUP BY groups_count
ORDER BY groups_count;
"""

group_query = """
WITH source_types AS (
    SELECT pbt.price_id, bt.std_id
    FROM public.price_body_types pbt
    JOIN public.body_types bt
        ON bt.id = pbt.body_type_id

    UNION

    SELECT p.id, bt.std_id
    FROM public.prices p
    JOIN public.body_types bt
        ON bt.id = p.body_type
    WHERE NOT EXISTS (
        SELECT 1
        FROM public.price_body_types pbt
        WHERE pbt.price_id = p.id
    )
),
standard_groups AS (
    SELECT DISTINCT
        price_id,
        CASE
            WHEN std_id = 56 THEN 'Тент'
            WHEN std_id = 4 THEN 'Рефрижератор'
            WHEN std_id = 2 THEN 'Изотерм'
            WHEN std_id = 15 THEN 'Борт'
            ELSE 'Прочие'
        END AS body_group
    FROM source_types
)
SELECT
    body_group,
    COUNT(DISTINCT price_id) AS prices_count
FROM standard_groups
GROUP BY body_group
ORDER BY prices_count DESC;
"""

with engine.connect() as connection:
    print("\n=============== Группы на одну перевозку ===============")
    df = pd.read_sql_query(text(query), connection)
    print(df.to_string(index=False))

    print("\n=============== Распределение стандартных групп ===============")
    df = pd.read_sql_query(text(group_query), connection)
    print(df.to_string(index=False))
