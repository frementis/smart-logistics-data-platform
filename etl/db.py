
import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()

password = os.getenv("POSTGRES_PASSWORD")
if not password:
    raise RuntimeError("POSTGRES_PASSWORD not found in .env")

try:
    port = int(os.getenv("POSTGRES_PORT", "5432"))
except ValueError as exc:
    raise RuntimeError("POSTGRES_PORT must be an integer") from exc

database_url = URL.create(
    drivername="postgresql+psycopg",
    username="app",
    password=password,
    host="localhost",
    port=port,
    database="deals_bigdata",
)

engine = create_engine(database_url, pool_pre_ping=True)
