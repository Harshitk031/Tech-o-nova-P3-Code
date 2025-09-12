# scripts/load_data.py
import os
import csv
import io
import psycopg2

# --- Connection Parameters (use your environment variables in a real app) ---
DB_PARAMS = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
    "dbname": "postgres"
}
 
# --- List of tables and their corresponding CSV files ---
TABLES_TO_LOAD = [
    ("olist_customers_dataset", "olist_customers_dataset.csv"),
    ("olist_orders_dataset", "olist_orders_dataset.csv"),
    ("olist_order_items_dataset", "olist_order_items_dataset.csv")
]

# Required CSV columns for each table (subset of original Olist dataset)
REQUIRED_COLUMNS = {
    "olist_customers_dataset": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state"
    ],
    "olist_orders_dataset": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp"
    ],
    "olist_order_items_dataset": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value"
    ]
}

def _prepare_csv_with_required_columns(source_csv_path, required_columns):
    """Create an in-memory CSV with only the required columns, preserving header.

    This avoids COPY errors like 'extra data after last expected column'
    when source CSVs contain additional fields.
    """
    with open(source_csv_path, 'r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {source_csv_path}")

        missing = [c for c in required_columns if c not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"Missing required columns {missing} in {os.path.basename(source_csv_path)}."
            )

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=required_columns)
        writer.writeheader()
        for row in reader:
            writer.writerow({col: row.get(col, "") for col in required_columns})

        buffer.seek(0)
        return buffer

def load_data():
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Get the absolute path to the project's root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for table_name, file_name in TABLES_TO_LOAD:
            file_path = os.path.join(project_root, 'hack_data', file_name)
            print(f"Loading data from '{file_name}' into table '{table_name}'...")

            # Prepare a CSV stream restricted to the columns our schema defines
            csv_stream = _prepare_csv_with_required_columns(
                file_path, REQUIRED_COLUMNS[table_name]
            )

            # Use psycopg2's copy_expert for efficient CSV loading
            sql_command = f"""
            COPY {table_name} ({', '.join(REQUIRED_COLUMNS[table_name])})
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
            """
            cur.copy_expert(sql=sql_command, file=csv_stream)

        conn.commit()
        cur.close()
        print("\nData loading complete!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    load_data()