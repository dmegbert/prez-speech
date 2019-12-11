from contextlib import contextmanager
import logging

import psycopg2
from psycopg2.extras import NamedTupleCursor

from src.config import db_conn_args


@contextmanager
def safe_cursor():
    try:
        conn = psycopg2.connect(**db_conn_args())
        try:
            cur = conn.cursor(cursor_factory=NamedTupleCursor)
            yield cur
        except Exception as e:
            conn.rollback()
            logging.error(f'db cursor error: {e}')
        finally:
            cur.close()
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f'db error: {e}')
    finally:
        conn.close()