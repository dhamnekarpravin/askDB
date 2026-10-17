USE askdb_shop;

CREATE TABLE IF NOT EXISTS query_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question VARCHAR(500) NOT NULL,
  generated_sql TEXT,
  success BOOLEAN NOT NULL,
  error_message VARCHAR(300),
  attempts INT,
  row_count INT,
  duration_ms INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The writer account manages history. The read-only account stays read-only.
GRANT SELECT, INSERT ON askdb_shop.query_history TO 'askdb_admin'@'localhost';
FLUSH PRIVILEGES;