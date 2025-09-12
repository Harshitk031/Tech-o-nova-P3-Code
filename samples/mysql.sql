-- samples/mysql.sql
CREATE DATABASE IF NOT EXISTS test;
USE test;

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    created_at DATETIME,
    amount DECIMAL(10, 2)
);

CREATE TABLE line_items (
    order_id INT,
    product_id INT,
    qty INT
);

INSERT INTO orders (customer_id, created_at, amount)
SELECT
    FLOOR(RAND() * 1000),
    NOW() - INTERVAL FLOOR(RAND() * 730) DAY,
    ROUND(RAND() * 500, 2)
FROM (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) a
JOIN (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) b
JOIN (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) c
JOIN (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) d
LIMIT 100000; -- Simple way to generate rows without a procedure