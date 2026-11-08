
import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

# Переменные из файла .env
load_dotenv()

# Получаем пароль PostgreSQL
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    raise RuntimeError("POSTGRES_PASSWORD не найден в файле .env")

# Адреса подключения
database_url = URL.create(
    drivername="postgresql+psycopg",
    username="app",
    password=password,
    host="localhost",
    port=5432,
    database="deals_bigdata",
)

# Объект подключения
engine = create_engine(
    database_url,
    pool_pre_ping=True,
)
