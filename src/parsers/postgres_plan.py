# src/parsers/postgres_plan.py
import re

def parse_postgres_plan(file_path):
    """
    Parses a PostgreSQL EXPLAIN (FORMAT JSON) file and extracts key metrics.
    """
    # Read the file with different encodings to handle potential issues
    content = None
    for encoding in ['utf-16', 'utf-8', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print("Error: Could not read file with any supported encoding")
        return

    print("--- PostgreSQL Plan Analysis ---")
    
    # Extract key metrics using simple string searches
    def extract_value(key, content):
        # Look for the key followed by a colon and extract the value
        pattern = f'"{key}":'
        start = content.find(pattern)
        if start == -1:
            return "Unknown"
        
        # Find the value after the colon
        value_start = content.find(':', start) + 1
        # Skip whitespace
        while value_start < len(content) and content[value_start] in ' \t\n':
            value_start += 1
        
        # Extract the value (string or number)
        if content[value_start] == '"':
            # String value
            end = content.find('"', value_start + 1)
            return content[value_start + 1:end] if end != -1 else "Unknown"
        else:
            # Numeric value
            end = value_start
            while end < len(content) and content[end] not in ',\n}':
                end += 1
            return content[value_start:end].strip()
    
    node_type = extract_value("Node Type", content)
    plan_rows = extract_value("Plan Rows", content)
    actual_rows = extract_value("Actual Rows", content)
    shared_read = extract_value("Shared Read Blocks", content)
    execution_time = extract_value("Execution Time", content)
    total_cost = extract_value("Total Cost", content)
    
    print(f"Node Type: {node_type}")
    print(f"Estimated Rows: {plan_rows}")
    print(f"Actual Rows: {actual_rows}")
    print(f"Shared Blocks Read: {shared_read}")
    print(f"Execution Time: {execution_time} ms")
    print(f"Total Cost: {total_cost}")

    # Example of identifying a "red flag"
    if node_type == 'Seq Scan':
        print("Red Flag: Sequential Scan detected on a filtered query.")

if __name__ == '__main__':
    # Use the original plan file
    parse_postgres_plan('artifacts/postgres/plans/pg_plan_1.json')
