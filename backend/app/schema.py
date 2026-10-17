import pymysql

from . import config

import time

HIDDEN_TABLES = {"query_history"}


def get_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_READONLY_USER,
        password=config.DB_READONLY_PASSWORD,
        database=config.DB_NAME,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_schema_text() -> str:
    """Return the schema as compact text the LLM can read."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (config.DB_NAME,),
            )
            columns = cur.fetchall(),
            columns = [c for c in columns if c["TABLE_NAME"] not in HIDDEN_TABLES]

            cur.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                """,
                (config.DB_NAME,),
            )
            fks = cur.fetchall()
    finally:
        conn.close()

    tables: dict[str, list[str]] = {}
    for c in columns:
        key = " PK" if c["COLUMN_KEY"] == "PRI" else ""
        tables.setdefault(c["TABLE_NAME"], []).append(
            f"{c['COLUMN_NAME']} {c['COLUMN_TYPE']}{key}"
        )

    lines = [f"{name}({', '.join(cols)})" for name, cols in tables.items()]
    lines.append("")
    lines.append("Foreign keys:")
    for fk in fks:
        lines.append(
            f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']} -> "
            f"{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}"
        )
    return "\n".join(lines)


def get_schema_dict() -> dict[str, set[str]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s",
                (config.DB_NAME,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    schema: dict[str, set[str]] = {}
    for r in rows:
        if r["TABLE_NAME"].lower() in HIDDEN_TABLES:
            continue
        schema.setdefault(r["TABLE_NAME"].lower(), set()).add(r["COLUMN_NAME"].lower())
        return schema

_cache: dict = {}



def _cached(key, loader):
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < config.SCHEMA_CACHE_SECONDS:
        return entry[1]
    value = loader()
    _cache[key] = (time.time(), value)
    return value


def cached_schema_text() -> str:
    return _cached("text", get_schema_text)


def cached_schema_dict() -> dict:
    return _cached("dict", get_schema_dict)