
from sqlalchemy import text

from etl.db import engine


with engine.connect() as connection:
    result = connection.execute(
        text("""
            SELECT
                current_database(),
                current_user,
                version()
        """)
    )

    database, user, version = result.fetchone()

    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"PostgreSQL: {version}")
