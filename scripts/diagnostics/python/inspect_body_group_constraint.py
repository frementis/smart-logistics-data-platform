
from sqlalchemy import text
from etl.db import engine

fix_query = r"""
ALTER TABLE core.price_body_groups
DROP CONSTRAINT IF EXISTS price_body_groups_body_group_check;

ALTER TABLE core.price_body_groups
ADD CONSTRAINT price_body_groups_body_group_check
CHECK (
    body_group IN (
        U&'\0422\0435\043D\0442',
        U&'\0420\0435\0444\0440\0438\0436\0435\0440\0430\0442\043E\0440',
        U&'\0418\0437\043E\0442\0435\0440\043C',
        U&'\0411\043E\0440\0442',
        U&'\041F\0440\043E\0447\0438\0435',
        U&'\041D\0435\0020\0443\043A\0430\0437\0430\043D'
    )
);
"""

check_query = text("""
    SELECT pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'core.price_body_groups'::regclass
      AND conname = 'price_body_groups_body_group_check';
""")

expected_groups = [
    "Тент",
    "Рефрижератор",
    "Изотерм",
    "Борт",
    "Прочие",
    "Не указан",
]

with engine.begin() as connection:
    connection.execute(text(fix_query))
    definition = connection.execute(check_query).scalar_one()

print("Проверка названий групп:")

for group in expected_groups:
    result = group in definition
    print(f"{group}: {result}")
