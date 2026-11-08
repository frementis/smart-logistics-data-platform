CREATE TABLE IF NOT EXISTS core.price_body_groups (
    price_id BIGINT NOT NULL
        REFERENCES core.prices(id) ON DELETE CASCADE,

    body_group VARCHAR(30) NOT NULL
        CHECK (
            body_group IN (
                'Тент',
                'Рефрижератор',
                'Изотерм',
                'Борт',
                'Прочие',
                'Не указан'
            )
        ),

    PRIMARY KEY (price_id, body_group)
);

CREATE INDEX IF NOT EXISTS idx_price_body_groups_body_group
    ON core.price_body_groups(body_group);
