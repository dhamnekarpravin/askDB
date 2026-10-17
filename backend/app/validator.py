import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

BLOCKED_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
    exp.Alter, exp.Command, exp.Merge, exp.TruncateTable,
)


class UnsafeSQLError(Exception):
    """The query was rejected. The message is safe to show and to feed back to the model."""


def validate_sql(sql: str, allowed_schema: dict[str, set[str]]) -> str:
    """Return the SQL if it is a single, safe SELECT on known tables and columns."""
    try:
        statements = sqlglot.parse(sql, read="mysql")
    except ParseError as e:
        raise UnsafeSQLError(f"SQL could not be parsed: {e}")

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise UnsafeSQLError("Exactly one SQL statement is allowed")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise UnsafeSQLError("Only SELECT queries are allowed")

    for node in tree.walk():
        if isinstance(node, BLOCKED_NODES):
            raise UnsafeSQLError("The query contains a forbidden operation")
        if isinstance(node, exp.Into):
            raise UnsafeSQLError("SELECT ... INTO is not allowed")

    # Table check
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    tables = {}
    for t in tree.find_all(exp.Table):
        name = t.name.lower()
        if name in cte_names:
            continue
        if name not in allowed_schema:
            raise UnsafeSQLError(f"Unknown table: {t.name}")
        tables[(t.alias_or_name or name).lower()] = name

    # Column check (only columns that name their table, or that exist in some used table)
    used_tables = set(tables.values())
    all_columns = set().union(*(allowed_schema[t] for t in used_tables)) if used_tables else set()
    select_aliases = {a.alias.lower() for a in tree.find_all(exp.Alias) if a.alias}

    for col in tree.find_all(exp.Column):
        cname = col.name.lower()
        if cname == "*":
            continue
        if col.table:
            real = tables.get(col.table.lower())
            if real and cname not in allowed_schema[real]:
                raise UnsafeSQLError(f"Unknown column: {col.table}.{col.name}")
        elif cname not in all_columns and cname not in select_aliases:
            raise UnsafeSQLError(f"Unknown column: {col.name}")

    return tree.sql(dialect="mysql")