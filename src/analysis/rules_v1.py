# src/analysis/rules_v1.py

# Let's assume you have placeholder functions for your parsers from previous steps.
# In a real app, you would import them:
# from src.parsers.postgres_plan import parse_postgres_plan
# from src.analysis.sql_features import extract_sql_features

def check_for_missing_index(plan_data, sql_features):
    """
    Rule: Detects a sequential scan on a table with a WHERE clause.

    Args:
        plan_data (dict): Parsed data from the EXPLAIN plan.
        sql_features (dict): Features extracted from the SQL query string.

    Returns:
        A recommendation dictionary if the rule matches, otherwise None.
    """
    recommendations = []

    # The core logic for the rule
    node_type = plan_data.get('Node Type')
    table_name = plan_data.get('Relation Name')
    where_columns = sql_features.get('where_columns')

    if node_type == 'Seq Scan' and where_columns:
        # Join column names for composite index suggestion, if applicable
        column_list = ", ".join(where_columns)
        index_name = f"idx_{table_name}_{'_'.join(where_columns)}"

        recommendation = {
            "type": "MISSING_INDEX",
            "rationale": f"The query performed a full table scan (Seq Scan) on '{table_name}' but has a filter on the column(s): {column_list}. This is highly inefficient.",
            "evidence_nodes": [plan_data],
            "suggested_action": f"CREATE INDEX {index_name} ON {table_name} ({column_list});",
            "caveats": "Verify index effectiveness with HypoPG or in a staging environment before applying to production."
        }
        recommendations.append(recommendation)

    return recommendations

if __name__ == '__main__':
    # --- This section simulates running your full pipeline ---

    # 1. Simulated data from your plan parser
    # In a real run, this would come from parse_postgres_plan()
    parsed_plan = {
        'Node Type': 'Seq Scan',
        'Relation Name': 'orders',
        'Total Cost': 1719.90,
        'Actual Rows': 99
    }

    # 2. Simulated data from your SQL feature extractor
    # In a real run, this would come from extract_sql_features()
    extracted_features = {
        'where_columns': ['customer_id']
    }

    # 3. Run the rules engine
    found_recommendations = check_for_missing_index(parsed_plan, extracted_features)

    # 4. Print the results
    if found_recommendations:
        print("--- ✅ Recommendation Generated ---")
        for rec in found_recommendations:
            for key, value in rec.items():
                print(f"- {key.replace('_', ' ').title()}: {value}")
    else:
        print("--- 🆗 No recommendations found for this plan. ---")



