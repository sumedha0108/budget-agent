from contextlib import contextmanager
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_conn():
    try:
        conn = psycopg.connect(DB_URL)
        yield conn
        conn.close()
    except psycopg.OperationalError as e:
        raise RuntimeError(f"Database connection failed: {e}")