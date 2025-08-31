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

    _num = re.compile(r'^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)', re.VERBOSE)
    def clean_and_convert(val):
        m = _num.match(str(val))
        return float(m.group(1)) if m else float('nan')


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

```python
def create_compose_map_figure(
    bin_df, bin_group_list, group_by, bin_coord_df, colorscale='Viridis'
):
    if bin_df.empty:
        return go.Figure()

    # mark rows that belong to the selected bin groups
    bin_df = bin_df.copy()
    bin_df['bin_group_count'] = bin_df['bin_group'].isin(bin_group_list).astype(int)

    # aggregate counts per (x, y, group)
    grouped = (bin_df.groupby(['chip_x_pos', 'chip_y_pos', group_by])
                      .agg(counts=('bin_group_count', 'sum'))
                      .reset_index())

    # ensure integer grid indices
    for c in ['chip_x_pos', 'chip_y_pos']:
        grouped[c] = grouped[c].astype(int)
        bin_coord_df[c] = bin_coord_df[c].astype(int)

    # list groups; sort if you want reproducible order
    unique_groups = sorted(grouped[group_by].unique().tolist())
    n = len(unique_groups)

    # --- dynamic grid: near-square layout ---
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=unique_groups)

    # compute global color range for a shared colorbar
    # (use 5–95% quantiles; fall back to min/max if identical)
    q5, q95 = grouped['counts'].quantile([0.05, 0.95])
    if q5 == q95:
        cmin, cmax = grouped['counts'].min(), grouped['counts'].max()
        if cmin == cmax:  # all zeros?
            cmin, cmax = 0, max(1, cmax)
    else:
        cmin, cmax = float(q5), float(q95)

    # shared coloraxis => single colorbar
    fig.update_layout(
        coloraxis=dict(
            colorscale=colorscale,
            cmin=cmin,
            cmax=cmax,
            colorbar=dict(title='Counts', tickfont=dict(size=10), thickness=14)
        ),
        margin=dict(l=20, r=20, t=40, b=10),
        showlegend=False
    )

    # draw one heatmap per group
    for i, g in enumerate(unique_groups):
        r = i // cols + 1
        c = i % cols + 1

        # left join to ensure full wafer grid, then pivot to 2D
        f = bin_coord_df.merge(
            grouped[grouped[group_by] == g],
            how='left',
            on=['chip_x_pos', 'chip_y_pos']
        ).fillna({'counts': 0})

        ztbl = f.pivot_table(
            index='chip_y_pos', columns='chip_x_pos', values='counts', fill_value=0
        )
        x_vals = list(ztbl.columns)
        y_vals = list(ztbl.index)
        z_vals = ztbl.values

        # 2D hovertext matching z’s shape
        hovertext = [
            [
                f"x: {x} | y: {y}<br>Counts: {z:.0f}"
                for x, z in zip(x_vals, z_row)
            ]
            for y, z_row in zip(y_vals, z_vals)
        ]

        fig.add_trace(
            go.Heatmap(
                z=z_vals,
                x=x_vals,
                y=y_vals,
                xgap=1, ygap=1,
                coloraxis="coloraxis",   # <-- shared colorbar
                hoverinfo='text',
                text=hovertext,
                hovertemplate="%{text}<extra></extra>",
            ),
            row=r, col=c
        )

        # tidy axes for each subplot
        fig.update_xaxes(title_text="X", tickfont=dict(size=9), row=r, col=c)
        fig.update_yaxes(title_text="Y", tickfont=dict(size=9), row=r, col=c, scaleanchor=None)

    # keep each cell square-ish per subplot
    # (global equal aspect is tricky across subplots; this keeps ticks readable)
    return fig

```python
    def fetch_with_images(
        cls,
        start_date: str,
        end_date: str,
        sba_days=None,
        alert_level=None,
        product=None,
        sba_type=None,
    ) -> pd.DataFrame:
        """
        Query SBA rows within [start_date, end_date] (inclusive), optionally filtered by
        sba_days / alert_level / product / sba_type. Join latest images by foreign_key
        from MapImage, TrendImage, RootCauseImage, and return a pandas DataFrame.

        Parameters
        ----------
        start_date : str
            Inclusive lower bound, 'YYYY-mm-dd'.
        end_date : str
            Inclusive upper bound, 'YYYY-mm-dd'.
        sba_days, alert_level, product, sba_type : str | list[str] | None
            Optional filters; pass a single value or a list of values.

        Returns
        -------
        pandas.DataFrame
        """

        # --- Parse dates (inclusive day range) ---
        s_dt = dt.datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = dt.datetime.strptime(end_date, "%Y-%m-%d") + dt.timedelta(days=1) - dt.timedelta(seconds=1)

        def _as_list(v):
            if v is None:
                return None
            if isinstance(v, (list, tuple, set)):
                return list(v)
            return [v]

        # --- Dynamic filters ---
        wheres = [
            cls.sba_date.is_null(False),
            cls.sba_date.between(s_dt, e_dt),
        ]

        vals = _as_list(sba_days)
        if vals:
            wheres.append(cls.sba_days.in_(vals) if len(vals) > 1 else (cls.sba_days == vals[0]))

        vals = _as_list(alert_level)
        if vals:
            wheres.append(cls.alert_level.in_(vals) if len(vals) > 1 else (cls.alert_level == vals[0]))

        vals = _as_list(product)
        if vals:
            wheres.append(cls.product.in_(vals) if len(vals) > 1 else (cls.product == vals[0]))

        vals = _as_list(sba_type)
        if vals:
            wheres.append(cls.sba_type.in_(vals) if len(vals) > 1 else (cls.sba_type == vals[0]))

        # --- Subqueries to get latest image id per foreign_key (by max id) ---
        # If you later add a timestamp column (e.g., created_at), replace fn.MAX(MapImage.id)
        # with fn.MAX(MapImage.created_at) and join on that instead.
        latest_map = (MapImage
                      .select(MapImage.foreign_key, fn.MAX(MapImage.id).alias('max_id'))
                      .group_by(MapImage.foreign_key)
                      .alias('latest_map'))

        latest_trend = (TrendImage
                        .select(TrendImage.foreign_key, fn.MAX(TrendImage.id).alias('max_id'))
                        .group_by(TrendImage.foreign_key)
                        .alias('latest_trend'))

        latest_root = (RootCauseImage
                       .select(RootCauseImage.foreign_key, fn.MAX(RootCauseImage.id).alias('max_id'))
                       .group_by(RootCauseImage.foreign_key)
                       .alias('latest_root'))

        # --- Build query with LEFT JOINs to subqueries, then to the actual rows ---
        q = (cls
             .select(
                 cls.id, cls.sba_type, cls.sba_date, cls.product, cls.alert_level,
                 cls.sba_days, cls.foreign_key,
                 MapImage.map_image.alias('map_image'),
                 TrendImage.trend_image.alias('trend_image'),
                 RootCauseImage.root_cause_image.alias('root_cause_image'),
             )
             # MapImage join
             .join(latest_map, JOIN.LEFT_OUTER, on=(cls.foreign_key == latest_map.c.foreign_key))
             .join(MapImage, JOIN.LEFT_OUTER, on=(MapImage.id == latest_map.c.max_id))
             .switch(cls)
             # TrendImage join
             .join(latest_trend, JOIN.LEFT_OUTER, on=(cls.foreign_key == latest_trend.c.foreign_key))
             .join(TrendImage, JOIN.LEFT_OUTER, on=(TrendImage.id == latest_trend.c.max_id))
             .switch(cls)
             # RootCauseImage join
             .join(latest_root, JOIN.LEFT_OUTER, on=(cls.foreign_key == latest_root.c.foreign_key))
             .join(RootCauseImage, JOIN.LEFT_OUTER, on=(RootCauseImage.id == latest_root.c.max_id))
             .where(*wheres)
             .order_by(cls.sba_date.desc(), cls.id.desc())
        )

        rows = list(q.dicts())
        # Ensure consistent columns if no rows
        if not rows:
            return pd.DataFrame(columns=[
                'id', 'sba_type', 'sba_date', 'product', 'alert_level', 'sba_days',
                'foreign_key', 'map_image', 'trend_image', 'root_cause_image'
            ])
        return pd.DataFrame(rows)
