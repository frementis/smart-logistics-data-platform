from etl.db import engine
from etl.body_groups import rebuild_price_body_groups


with engine.begin() as connection:
    inserted_count = rebuild_price_body_groups(connection)

print(f"Пересборка групп кузовов завершена.")
print(f"Создано связей: {inserted_count}")