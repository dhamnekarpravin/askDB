-- Writer account: only for loading data (never used by the app)
CREATE USER IF NOT EXISTS 'askdb_admin'@'localhost' IDENTIFIED BY 'admin_pass_123';
GRANT ALL PRIVILEGES ON askdb_shop.* TO 'askdb_admin'@'localhost';

-- Read-only account: used by the app to run generated SQL
CREATE USER IF NOT EXISTS 'askdb_ro'@'localhost' IDENTIFIED BY 'ro_pass_123';
GRANT SELECT ON askdb_shop.* TO 'askdb_ro'@'localhost';

FLUSH PRIVILEGES;