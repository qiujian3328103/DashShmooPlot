def query_latest_records(db_name, table_name, foreign_keys):
    # Connect to DuckDB using Ibis.
    con = ibis.connect(f"duckdb://{db_name}")
    # Reference the table.
    table = con.table(table_name)
    
    # Filter rows to only include those with foreign keys in the provided list.
    filtered = table.filter(table.foregin_key.isin(foreign_keys))
    
    # Create a window partitioned by 'foregin_key' and ordered by 'last_update_time' descending.
    window_spec = ibis.window(group_by="foregin_key", order_by=ibis.desc("last_update_time"))
    
    # Add a row number to each row within its foreign key group.
    ranked = filtered.mutate(row_num=ibis.row_number().over(window_spec))
    
    # Filter to keep only the first (latest) record for each foreign key.
    latest = ranked.filter(ranked.row_num == 1)
    
    # Execute the query and return the result as a pandas DataFrame.
    return latest.execute()
