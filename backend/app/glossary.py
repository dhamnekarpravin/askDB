GLOSSARY = """
Business rules:
- "Revenue" or "sales" means SUM(order_items.quantity * order_items.unit_price) for orders with status = 'PAID'.
- Orders with status 'CANCELLED' or 'PENDING' never count as revenue.
- "Customer" refers to the customers table; "this year" means the current calendar year.
- Order status values are exactly: PAID, PENDING, CANCELLED.
"""

