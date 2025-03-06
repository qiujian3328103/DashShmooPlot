```python
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
```

```python
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.feature_selection import mutual_info_regression
from minepy import MINE
import dcor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

def compute_correlations(df, x_col='X'):
    """
    Compute various correlation/dependency metrics between X and each Y column.
    
    Parameters:
      df    : pandas DataFrame containing the data.
      x_col : string, name of the target column (default 'X').
    
    Returns:
      A pandas DataFrame with one row per Y column and columns for each metric.
    """
    results = []
    # Consider all columns except x_col as candidate Y columns.
    y_cols = [col for col in df.columns if col != x_col]
    
    for y_col in y_cols:
        # Drop any missing values for a fair comparison.
        valid = df[[x_col, y_col]].dropna()
        x_vals = valid[x_col].values
        y_vals = valid[y_col].values
        
        # 1. Pearson correlation (linear)
        pearson_corr, _ = pearsonr(x_vals, y_vals)
        
        # 2. Spearman correlation (monotonic, rank-based)
        spearman_corr, _ = spearmanr(x_vals, y_vals)
        
        # 3. Kendall's tau (ordinal association)
        kendall_corr, _ = kendalltau(x_vals, y_vals)
        
        # 4. Mutual Information (general dependency)
        # mutual_info_regression expects a 2D array for features.
        mi = mutual_info_regression(valid[[y_col]], valid[x_col], random_state=0)
        mi_val = mi[0]
        
        # 5. Maximal Information Coefficient (MIC)
        mine = MINE(alpha=0.6, c=15)
        mine.compute_score(x_vals, y_vals)
        mic = mine.mic()
        
        # 6. Distance Correlation
        d_corr = dcor.distance_correlation(x_vals, y_vals)
        
        # 7. Model-based approach using Random Forest (univariate prediction)
        rf = RandomForestRegressor(random_state=0)
        # Use the candidate y as predictor to forecast X.
        rf.fit(valid[[y_col]], valid[x_col])
        y_pred = rf.predict(valid[[y_col]])
        r2 = r2_score(valid[x_col], y_pred)
        
        results.append({
            'y_col': y_col,
            'pearson_corr': pearson_corr,
            'spearman_corr': spearman_corr,
            'kendall_corr': kendall_corr,
            'mutual_info': mi_val,
            'mic': mic,
            'distance_corr': d_corr,
            'rf_r2': r2
        })
        
    return pd.DataFrame(results)

# Example usage:
if __name__ == '__main__':
    # Create some example data.
    np.random.seed(0)
    n = 1000
    df = pd.DataFrame({
        'X': np.random.rand(n),
        'y1': np.random.rand(n),
        'y2': np.random.rand(n),
        'y3': np.random.rand(n)
    })
    
    # Compute all metrics.
    results_df = compute_correlations(df, x_col='X')
    
    # Optionally, sort by one of the metrics (e.g., model R² score) to rank the predictors.
    sorted_results = results_df.sort_values(by='rf_r2', ascending=False)
    
    print(sorted_results)
```
