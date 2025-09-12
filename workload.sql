-- workload.sql

-- Query 1: Inefficient Filter (will cause a full table scan)
SELECT * FROM olist_orders_dataset WHERE order_status = 'delivered';

-- Query 2: Large JOIN (tests join performance)
SELECT o.order_id, o.order_status, c.customer_city, c.customer_state
FROM olist_orders_dataset o
JOIN olist_customers_dataset c ON o.customer_id = c.customer_id
WHERE c.customer_state = 'SP';

-- Query 3: Aggregation and Sorting (tests grouping)
SELECT c.customer_state, COUNT(o.order_id) as order_count
FROM olist_orders_dataset o
JOIN olist_customers_dataset c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY order_count DESC;