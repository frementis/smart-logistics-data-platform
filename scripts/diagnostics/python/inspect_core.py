
import pandas as pd
from sqlalchemy import text
from etl.db import engine

query = """
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'core'
ORDER BY table_name, ordinal_position;
"""

with engine.connect() as connection:
    df = pd.read_sql_query(text(query), connection)
    print(df.to_string(index=False))
