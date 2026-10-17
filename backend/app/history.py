import logging

import pymysql

from . import config

log = logging.getLogger("askdb")


def _writer_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_WRITER_USER,
        password=config.DB_WRITER_PASSWORD,
        database=config.DB_NAME,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def save_history(question, sql, success, error_message, attempts, row_count, duration_ms):
    """History is a bonus: if saving fails, log it and carry on."""
    try:
        conn = _writer_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO query_history "
                    "(question, generated_sql, success, error_message, attempts, row_count, duration_ms) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (question, sql, success, (error_message or "")[:300] or None,
                     attempts, row_count, duration_ms),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        log.error("Could not save history: %s", e)


def get_history(limit: int = 20):
    conn = _writer_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, question, generated_sql, success, error_message, attempts, "
                "row_count, duration_ms, created_at "
                "FROM query_history ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat()
    return rows