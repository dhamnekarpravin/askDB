from decimal import Decimal
from datetime import date, datetime

import pymysql

from . import config
from .schema import get_connection


class QueryExecutionError(Exception):
    """The database rejected or failed the query. Safe to feed back to the model."""


def _jsonable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def run_query(sql: str) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Server-side timeout for SELECTs, in milliseconds
            cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {config.QUERY_TIMEOUT_SECONDS * 1000}")
            cur.execute(sql)
            rows = cur.fetchmany(config.MAX_ROWS + 1)
            columns = [c[0] for c in cur.description] if cur.description else []
    except pymysql.err.MySQLError as e:
        raise QueryExecutionError(f"Database error: {e.args[-1] if e.args else 'query failed'}")
    finally:
        conn.close()

    truncated = len(rows) > config.MAX_ROWS
    rows = rows[: config.MAX_ROWS]
    return {
        "columns": columns,
        "rows": [{k: _jsonable(v) for k, v in row.items()} for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }