-- samples/postgres.sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT,
    created_at TIMESTAMPTZ,
    amount DECIMAL(10, 2)
);

CREATE TABLE line_items (
    order_id INT,
    product_id INT,
    qty INT
);

INSERT INTO orders (customer_id, created_at, amount)
SELECT
    (random() * 1000)::int,
    NOW() - (random() * 365 * 2) * '1 day'::interval,
    (random() * 500)::decimal(10, 2)
FROM generate_series(1, 100000);

INSERT INTO line_items(order_id, product_id, qty)
SELECT
    (random() * 100000)::int + 1,
    (random() * 200)::int,
    (random() * 5)::int + 1
FROM generate_series(1, 250000);