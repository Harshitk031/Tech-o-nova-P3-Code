-- scripts/setup_schema.sql

-- Drop tables if they exist to allow for a clean rerun
DROP TABLE IF EXISTS olist_order_items_dataset;
DROP TABLE IF EXISTS olist_orders_dataset;
DROP TABLE IF EXISTS olist_customers_dataset;

-- Create the tables
CREATE TABLE olist_customers_dataset (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix INT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE olist_orders_dataset (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP
);

CREATE TABLE olist_order_items_dataset (
    order_id TEXT,
    order_item_id INT,
    product_id TEXT,
    seller_id TEXT,
    price REAL,
    freight_value REAL
);