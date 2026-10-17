USE askdb_shop;

INSERT INTO customers (name, email, city, created_at) VALUES
('Rahul Sharma',  'rahul@example.com',  'Chennai',   '2025-01-15'),
('Priya Nair',    'priya@example.com',  'Bengaluru', '2025-02-03'),
('Anita Verma',   'anita@example.com',  'Mumbai',    '2025-02-20'),
('Karthik Raj',   'karthik@example.com','Chennai',   '2025-03-11'),
('Sneha Iyer',    'sneha@example.com',  'Hyderabad', '2025-04-02'),
('Vikram Singh',  'vikram@example.com', 'Delhi',     '2025-05-18'),
('Meera Das',     'meera@example.com',  'Kolkata',   '2025-06-07'),
('Arjun Menon',   'arjun@example.com',  'Bengaluru', '2025-07-25');

INSERT INTO products (name, category, price) VALUES
('Laptop',           'Electronics', 55000.00),
('Smartphone',       'Electronics', 20000.00),
('Headphones',       'Electronics',  3000.00),
('Office Chair',     'Furniture',    8500.00),
('Standing Desk',    'Furniture',   22000.00),
('Notebook Pack',    'Stationery',    250.00),
('Water Bottle',     'Lifestyle',     600.00),
('Backpack',         'Lifestyle',    1800.00);

INSERT INTO orders (customer_id, order_date, status) VALUES
(1, '2026-01-10', 'PAID'),
(1, '2026-03-05', 'PAID'),
(2, '2026-01-22', 'PAID'),
(3, '2026-02-14', 'CANCELLED'),
(4, '2026-02-28', 'PAID'),
(4, '2026-04-15', 'PENDING'),
(5, '2026-03-19', 'PAID'),
(6, '2026-05-02', 'PAID'),
(7, '2026-05-20', 'PAID'),
(8, '2026-06-11', 'PAID'),
(2, '2026-07-04', 'PAID'),
(1, '2026-08-09', 'PAID');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 55000.00), (1, 3, 1, 3000.00),
(2, 2, 1, 20000.00),
(3, 4, 2, 8500.00),
(4, 5, 1, 22000.00),
(5, 2, 1, 20000.00), (5, 7, 2, 600.00),
(6, 8, 1, 1800.00),
(7, 1, 1, 55000.00),
(8, 6, 10, 250.00), (8, 7, 1, 600.00),
(9, 5, 1, 22000.00), (9, 3, 2, 3000.00),
(10, 8, 2, 1800.00),
(11, 2, 1, 20000.00), (11, 6, 5, 250.00),
(12, 4, 1, 8500.00);