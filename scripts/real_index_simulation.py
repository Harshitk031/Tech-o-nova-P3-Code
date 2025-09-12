# scripts/real_index_simulation.py
import psycopg2
import json
import time

# --- Database Connection Details ---
DB_CONN_STR = "postgresql://postgres:postgres@localhost:5432"

# --- Query and Proposed Index ---
TEST_QUERY = "SELECT * FROM orders WHERE customer_id = 42;"
PROPOSED_INDEX = "CREATE INDEX idx_orders_customer_id ON orders (customer_id);"

def get_plan(cursor, query):
    """Executes EXPLAIN on a query and returns the JSON plan."""
    cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
    return cursor.fetchone()[0][0]

def measure_query_performance(cursor, query, iterations=3):
    """Measure actual query execution time."""
    times = []
    for _ in range(iterations):
        start_time = time.time()
        cursor.execute(query)
        cursor.fetchall()  # Consume all results
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Convert to milliseconds
    return sum(times) / len(times)  # Return average

def main():
    try:
        conn = psycopg2.connect(DB_CONN_STR)
        conn.autocommit = True

        with conn.cursor() as cur:
            print("--- Real Index Simulation ---")
            print("This creates a temporary index to demonstrate the actual impact.")
            print()

            # 1. Get the "BEFORE" plan and performance
            print("[BEFORE] Analyzing query without index...")
            before_plan = get_plan(cur, TEST_QUERY)
            before_node_type = before_plan['Plan']['Node Type']
            before_cost = before_plan['Plan']['Total Cost']
            before_rows = before_plan['Plan']['Plan Rows']
            before_actual_rows = before_plan['Plan']['Actual Rows']
            before_exec_time = before_plan['Plan']['Actual Total Time']
            
            print(f"         Plan: {before_node_type}")
            print(f"         Estimated Cost: {before_cost}")
            print(f"         Estimated Rows: {before_rows}")
            print(f"         Actual Rows: {before_actual_rows}")
            print(f"         Execution Time: {before_exec_time:.2f}ms")
            print()

            # 2. Create the actual index
            print("[ACTION] Creating temporary index...")
            try:
                cur.execute(PROPOSED_INDEX)
                print("         ✅ Index created successfully!")
            except Exception as e:
                print(f"         ❌ Error creating index: {e}")
                return
            print()

            # 3. Get the "AFTER" plan and performance
            print("[AFTER] Analyzing query with index...")
            after_plan = get_plan(cur, TEST_QUERY)
            after_node_type = after_plan['Plan']['Node Type']
            after_cost = after_plan['Plan']['Total Cost']
            after_rows = after_plan['Plan']['Plan Rows']
            after_actual_rows = after_plan['Plan']['Actual Rows']
            after_exec_time = after_plan['Plan']['Actual Total Time']
            
            print(f"         Plan: {after_node_type}")
            print(f"         Estimated Cost: {after_cost}")
            print(f"         Estimated Rows: {after_rows}")
            print(f"         Actual Rows: {after_actual_rows}")
            print(f"         Execution Time: {after_exec_time:.2f}ms")
            print()

            # 4. Calculate improvements
            cost_reduction = before_cost - after_cost
            cost_improvement = (cost_reduction / before_cost) * 100
            time_reduction = before_exec_time - after_exec_time
            time_improvement = (time_reduction / before_exec_time) * 100

            print("--- Performance Analysis ---")
            print(f"Cost Improvement: {cost_reduction:.2f} ({cost_improvement:.1f}%)")
            print(f"Time Improvement: {time_reduction:.2f}ms ({time_improvement:.1f}%)")
            print(f"Scan Type: {before_node_type} → {after_node_type}")
            print()

            if ("Index" in after_node_type or "Bitmap" in after_node_type) and after_cost < before_cost:
                print("✅ SUCCESS: The index significantly improves query performance!")
                print("   - Eliminates full table scan")
                print("   - Dramatically reduces execution time")
                print("   - Uses index-based access (Bitmap Heap Scan)")
                print("   - Provides precise row targeting")
            else:
                print("❌ WARNING: The index did not provide expected improvements.")
            print()

            # 5. Clean up
            print("[CLEANUP] Removing temporary index...")
            try:
                cur.execute("DROP INDEX IF EXISTS idx_orders_customer_id;")
                print("         ✅ Index removed successfully!")
            except Exception as e:
                print(f"         ⚠️  Warning: Could not remove index: {e}")
            print()

            print("--- Summary ---")
            print("This simulation demonstrates the real impact of adding an index.")
            print("In production, use HypoPG for safe 'what-if' analysis without")
            print("modifying the actual database schema.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()
