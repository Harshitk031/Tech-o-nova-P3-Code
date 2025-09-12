# src/parsers/mysql_plan.py
import json

def parse_mysql_plan(file_path):
    """
    Parses a MySQL EXPLAIN FORMAT=JSON file and extracts key metrics.
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
    
    # Clean up the content - remove "EXPLAIN" prefix and unescape newlines
    if content.startswith('EXPLAIN'):
        content = content[7:].strip()  # Remove "EXPLAIN" prefix
    
    # Unescape newlines and clean up
    content = content.replace('\\n', '\n').replace('\\t', '\t')
    
    # Parse the JSON
    data = json.loads(content)

    # The main query block contains the plan details
    plan_details = data['query_block']['table']

    print("\n--- MySQL Plan Analysis ---")
    print(f"Access Type: {plan_details.get('access_type')}")
    print(f"Rows Examined per Scan: {plan_details.get('rows_examined_per_scan')}")
    print(f"Filtered Percentage: {plan_details.get('filtered')}")

    # Example of identifying a "red flag"
    if plan_details.get('access_type') == 'ALL':
        print("Red Flag: Full Table Scan detected (access_type is ALL).")


if __name__ == '__main__':
    # Use the plan file you generated earlier
    parse_mysql_plan('artifacts/mysql/plans/mysql_plan_1.json')
