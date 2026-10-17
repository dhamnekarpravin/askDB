from app.validator import UnsafeSQLError, validate_sql

schema = {
    "customers": {"id", "name", "email", "city", "created_at"},
    "orders": {"id", "customer_id", "order_date", "status"},
}

good = [
    "SELECT * FROM customers",
    "SELECT c.name, COUNT(*) AS n FROM customers c JOIN orders o ON o.customer_id = c.id GROUP BY c.name",
]
bad = [
    "DROP TABLE customers",
    "DELETE FROM orders",
    "SELECT 1; DROP TABLE customers",
    "UPDATE customers SET name='x'",
    "SELECT * FROM mysql.user",
    "SELECT salary FROM customers",
    "SELECT * FROM customers INTO OUTFILE '/tmp/x'",
    "INSERT INTO customers (name) VALUES ('x')",
]

for q in good:
    validate_sql(q, schema)
    print("PASS (allowed):", q[:60])

for q in bad:
    try:
        validate_sql(q, schema)
        print("FAIL (should be blocked):", q)
    except UnsafeSQLError as e:
        print("PASS (blocked):", q[:50], "->", e)