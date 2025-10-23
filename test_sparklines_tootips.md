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


```XML
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>900</width>
    <height>600</height>
   </rect>
  </property>
  <property name="minimumSize">
   <size>
    <width>0</width>
    <height>0</height>
   </size>
  </property>
  <property name="maximumSize">
   <size>
    <width>16777215</width>
    <height>16777215</height>
   </size>
  </property>
  <property name="windowTitle">
   <string>INK File Converter</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <layout class="QGridLayout" name="gridLayout_5">
    <item row="0" column="0">
     <widget class="QSplitter" name="splitter">
      <property name="orientation">
       <enum>Qt::Orientation::Horizontal</enum>
      </property>
      <widget class="QGroupBox" name="groupBox_2">
       <property name="maximumSize">
        <size>
         <width>300</width>
         <height>16777215</height>
        </size>
       </property>
       <property name="title">
        <string/>
       </property>
       <layout class="QGridLayout" name="gridLayout_4">
        <item row="0" column="0">
         <layout class="QVBoxLayout" name="verticalLayout_2">
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout">
            <item>
             <widget class="QPushButton" name="pushButton_open_folder">
              <property name="text">
               <string>Open Folder</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout_4">
            <item>
             <widget class="QLineEdit" name="lineEdit_save_file_path">
              <property name="styleSheet">
               <string notr="true">background-color: rgb(255, 255, 255);</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QPushButton" name="pushButton_save_file_path">
              <property name="text">
               <string>Save Path</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout_2">
            <item>
             <widget class="QLabel" name="label">
              <property name="minimumSize">
               <size>
                <width>100</width>
                <height>0</height>
               </size>
              </property>
              <property name="text">
               <string>GOOD DIE: -----&gt;</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QLineEdit" name="lineEdit_good_die_output">
              <property name="styleSheet">
               <string notr="true">background-color: rgb(255, 255, 255);</string>
              </property>
              <property name="text">
               <string>1</string>
              </property>
              <property name="placeholderText">
               <string>Map value</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout_3">
            <item>
             <widget class="QLabel" name="label_2">
              <property name="minimumSize">
               <size>
                <width>100</width>
                <height>0</height>
               </size>
              </property>
              <property name="text">
               <string>FAILE DIE: -----&gt;</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QLineEdit" name="lineEdit_fail_die_output">
              <property name="styleSheet">
               <string notr="true">background-color: rgb(255, 255, 255);</string>
              </property>
              <property name="text">
               <string>X</string>
              </property>
              <property name="placeholderText">
               <string>Map value</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout_13">
            <item>
             <widget class="QLabel" name="label_11">
              <property name="minimumSize">
               <size>
                <width>100</width>
                <height>0</height>
               </size>
              </property>
              <property name="text">
               <string>Emty Space: ----&gt;</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QLineEdit" name="lineEdit_empty_output">
              <property name="styleSheet">
               <string notr="true">background-color: rgb(255, 255, 255);</string>
              </property>
              <property name="text">
               <string>.</string>
              </property>
              <property name="placeholderText">
               <string>Map value</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <layout class="QHBoxLayout" name="horizontalLayout_14">
            <item>
             <widget class="QLabel" name="label_12">
              <property name="minimumSize">
               <size>
                <width>100</width>
                <height>0</height>
               </size>
              </property>
              <property name="text">
               <string>Good Die List: </string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QLineEdit" name="lineEdit_good_die_list">
              <property name="toolTip">
               <string>use ',' to split</string>
              </property>
              <property name="styleSheet">
               <string notr="true">background-color: rgb(255, 255, 255);</string>
              </property>
              <property name="text">
               <string>0001</string>
              </property>
              <property name="placeholderText">
               <string>Map value</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item>
           <widget class="QGroupBox" name="groupBox">
            <property name="title">
             <string>Input File List</string>
            </property>
            <layout class="QGridLayout" name="gridLayout">
             <item row="0" column="0">
              <widget class="QListWidget" name="listWidget_file_list">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="selectionMode">
                <enum>QAbstractItemView::SelectionMode::MultiSelection</enum>
               </property>
              </widget>
             </item>
             <item row="1" column="0">
              <widget class="QPushButton" name="pushButton_convert_file">
               <property name="text">
                <string>Convert File</string>
               </property>
              </widget>
             </item>
            </layout>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </widget>
      <widget class="QTabWidget" name="tabWidget">
       <property name="currentIndex">
        <number>1</number>
       </property>
       <widget class="QWidget" name="tab">
        <attribute name="title">
         <string>Preview</string>
        </attribute>
        <layout class="QGridLayout" name="gridLayout_2">
         <item row="0" column="0">
          <widget class="QTextEdit" name="textEdit_preview"/>
         </item>
        </layout>
       </widget>
       <widget class="QWidget" name="tab_2">
        <attribute name="title">
         <string>Setting</string>
        </attribute>
        <layout class="QGridLayout" name="gridLayout_3">
         <item row="0" column="0">
          <layout class="QVBoxLayout" name="verticalLayout">
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_6">
             <item>
              <widget class="QLabel" name="label_3">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Lot ID:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QCheckBox" name="checkBox_extract_root_lot_id">
               <property name="toolTip">
                <string>Extract Root Lot ID uncheck will extract lot id</string>
               </property>
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="text">
                <string>Extract Root Lot ID         </string>
               </property>
               <property name="checked">
                <bool>true</bool>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_5">
             <item>
              <widget class="QLabel" name="label_4">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Wafer ID:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QCheckBox" name="checkBox_extract_wafer_id">
               <property name="toolTip">
                <string>Extract Root Lot ID uncheck will extract lot id</string>
               </property>
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="text">
                <string>Remove 'W' on WaferID</string>
               </property>
               <property name="checked">
                <bool>true</bool>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_7">
             <item>
              <widget class="QLabel" name="label_5">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Lot Wafer Location:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QSpinBox" name="spinBox_lot_wafer_location">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_8">
             <item>
              <widget class="QLabel" name="label_6">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Part ID Location:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QSpinBox" name="spinBox_part_id_location">
               <property name="toolTip">
                <string>row number where the part id located</string>
               </property>
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="value">
                <number>2</number>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_9">
             <item>
              <widget class="QLabel" name="label_7">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>FLAT:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QSpinBox" name="spinBox_flat">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_10">
             <item>
              <widget class="QLabel" name="label_8">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>X Coordinate Keyword:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QLineEdit" name="lineEdit_x_coord_keyword">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="text">
                <string>X=</string>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_11">
             <item>
              <widget class="QLabel" name="label_9">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Y Coordinate Keyword:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QLineEdit" name="lineEdit_y_coord_keyword">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="text">
                <string>Y=</string>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <layout class="QHBoxLayout" name="horizontalLayout_12">
             <item>
              <widget class="QLabel" name="label_10">
               <property name="minimumSize">
                <size>
                 <width>150</width>
                 <height>0</height>
                </size>
               </property>
               <property name="maximumSize">
                <size>
                 <width>150</width>
                 <height>16777215</height>
                </size>
               </property>
               <property name="text">
                <string>Bin Keyword:</string>
               </property>
              </widget>
             </item>
             <item>
              <widget class="QLineEdit" name="lineEdit_bin_keyword">
               <property name="styleSheet">
                <string notr="true">background-color: rgb(255, 255, 255);</string>
               </property>
               <property name="text">
                <string>B=</string>
               </property>
              </widget>
             </item>
            </layout>
           </item>
           <item>
            <spacer name="verticalSpacer">
             <property name="orientation">
              <enum>Qt::Orientation::Vertical</enum>
             </property>
             <property name="sizeHint" stdset="0">
              <size>
               <width>20</width>
               <height>178</height>
              </size>
             </property>
            </spacer>
           </item>
          </layout>
         </item>
        </layout>
       </widget>
      </widget>
     </widget>
    </item>
   </layout>
  </widget>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>900</width>
     <height>22</height>
    </rect>
   </property>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
 </widget>
 <resources/>
 <connections/>
</ui>


```python
# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 600)
        MainWindow.setMinimumSize(QtCore.QSize(0, 0))
        MainWindow.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.splitter)
        self.groupBox_2.setMaximumSize(QtCore.QSize(300, 16777215))
        self.groupBox_2.setTitle("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_open_folder = QtWidgets.QPushButton(parent=self.groupBox_2)
        self.pushButton_open_folder.setObjectName("pushButton_open_folder")
        self.horizontalLayout.addWidget(self.pushButton_open_folder)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lineEdit_save_file_path = QtWidgets.QLineEdit(parent=self.groupBox_2)
        self.lineEdit_save_file_path.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_save_file_path.setObjectName("lineEdit_save_file_path")
        self.horizontalLayout_4.addWidget(self.lineEdit_save_file_path)
        self.pushButton_save_file_path = QtWidgets.QPushButton(parent=self.groupBox_2)
        self.pushButton_save_file_path.setObjectName("pushButton_save_file_path")
        self.horizontalLayout_4.addWidget(self.pushButton_save_file_path)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.groupBox_2)
        self.label.setMinimumSize(QtCore.QSize(100, 0))
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit_good_die_output = QtWidgets.QLineEdit(parent=self.groupBox_2)
        self.lineEdit_good_die_output.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_good_die_output.setObjectName("lineEdit_good_die_output")
        self.horizontalLayout_2.addWidget(self.lineEdit_good_die_output)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(parent=self.groupBox_2)
        self.label_2.setMinimumSize(QtCore.QSize(100, 0))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.lineEdit_fail_die_output = QtWidgets.QLineEdit(parent=self.groupBox_2)
        self.lineEdit_fail_die_output.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_fail_die_output.setObjectName("lineEdit_fail_die_output")
        self.horizontalLayout_3.addWidget(self.lineEdit_fail_die_output)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_11 = QtWidgets.QLabel(parent=self.groupBox_2)
        self.label_11.setMinimumSize(QtCore.QSize(100, 0))
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_13.addWidget(self.label_11)
        self.lineEdit_empty_output = QtWidgets.QLineEdit(parent=self.groupBox_2)
        self.lineEdit_empty_output.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_empty_output.setObjectName("lineEdit_empty_output")
        self.horizontalLayout_13.addWidget(self.lineEdit_empty_output)
        self.verticalLayout_2.addLayout(self.horizontalLayout_13)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.label_12 = QtWidgets.QLabel(parent=self.groupBox_2)
        self.label_12.setMinimumSize(QtCore.QSize(100, 0))
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_14.addWidget(self.label_12)
        self.lineEdit_good_die_list = QtWidgets.QLineEdit(parent=self.groupBox_2)
        self.lineEdit_good_die_list.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_good_die_list.setObjectName("lineEdit_good_die_list")
        self.horizontalLayout_14.addWidget(self.lineEdit_good_die_list)
        self.verticalLayout_2.addLayout(self.horizontalLayout_14)
        self.groupBox = QtWidgets.QGroupBox(parent=self.groupBox_2)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.listWidget_file_list = QtWidgets.QListWidget(parent=self.groupBox)
        self.listWidget_file_list.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.listWidget_file_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.listWidget_file_list.setObjectName("listWidget_file_list")
        self.gridLayout.addWidget(self.listWidget_file_list, 0, 0, 1, 1)
        self.pushButton_convert_file = QtWidgets.QPushButton(parent=self.groupBox)
        self.pushButton_convert_file.setObjectName("pushButton_convert_file")
        self.gridLayout.addWidget(self.pushButton_convert_file, 1, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.gridLayout_4.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        self.tabWidget = QtWidgets.QTabWidget(parent=self.splitter)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.textEdit_preview = QtWidgets.QTextEdit(parent=self.tab)
        self.textEdit_preview.setObjectName("textEdit_preview")
        self.gridLayout_2.addWidget(self.textEdit_preview, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_3 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_3.setMinimumSize(QtCore.QSize(150, 0))
        self.label_3.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_6.addWidget(self.label_3)
        self.checkBox_extract_root_lot_id = QtWidgets.QCheckBox(parent=self.tab_2)
        self.checkBox_extract_root_lot_id.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.checkBox_extract_root_lot_id.setChecked(True)
        self.checkBox_extract_root_lot_id.setObjectName("checkBox_extract_root_lot_id")
        self.horizontalLayout_6.addWidget(self.checkBox_extract_root_lot_id)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_4 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_4.setMinimumSize(QtCore.QSize(150, 0))
        self.label_4.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_5.addWidget(self.label_4)
        self.checkBox_extract_wafer_id = QtWidgets.QCheckBox(parent=self.tab_2)
        self.checkBox_extract_wafer_id.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.checkBox_extract_wafer_id.setChecked(True)
        self.checkBox_extract_wafer_id.setObjectName("checkBox_extract_wafer_id")
        self.horizontalLayout_5.addWidget(self.checkBox_extract_wafer_id)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_5 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_5.setMinimumSize(QtCore.QSize(150, 0))
        self.label_5.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_7.addWidget(self.label_5)
        self.spinBox_lot_wafer_location = QtWidgets.QSpinBox(parent=self.tab_2)
        self.spinBox_lot_wafer_location.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.spinBox_lot_wafer_location.setObjectName("spinBox_lot_wafer_location")
        self.horizontalLayout_7.addWidget(self.spinBox_lot_wafer_location)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_6 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_6.setMinimumSize(QtCore.QSize(150, 0))
        self.label_6.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_8.addWidget(self.label_6)
        self.spinBox_part_id_location = QtWidgets.QSpinBox(parent=self.tab_2)
        self.spinBox_part_id_location.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.spinBox_part_id_location.setProperty("value", 2)
        self.spinBox_part_id_location.setObjectName("spinBox_part_id_location")
        self.horizontalLayout_8.addWidget(self.spinBox_part_id_location)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_7 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_7.setMinimumSize(QtCore.QSize(150, 0))
        self.label_7.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_9.addWidget(self.label_7)
        self.spinBox_flat = QtWidgets.QSpinBox(parent=self.tab_2)
        self.spinBox_flat.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.spinBox_flat.setObjectName("spinBox_flat")
        self.horizontalLayout_9.addWidget(self.spinBox_flat)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_8 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_8.setMinimumSize(QtCore.QSize(150, 0))
        self.label_8.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_10.addWidget(self.label_8)
        self.lineEdit_x_coord_keyword = QtWidgets.QLineEdit(parent=self.tab_2)
        self.lineEdit_x_coord_keyword.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_x_coord_keyword.setObjectName("lineEdit_x_coord_keyword")
        self.horizontalLayout_10.addWidget(self.lineEdit_x_coord_keyword)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_9 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_9.setMinimumSize(QtCore.QSize(150, 0))
        self.label_9.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_11.addWidget(self.label_9)
        self.lineEdit_y_coord_keyword = QtWidgets.QLineEdit(parent=self.tab_2)
        self.lineEdit_y_coord_keyword.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_y_coord_keyword.setObjectName("lineEdit_y_coord_keyword")
        self.horizontalLayout_11.addWidget(self.lineEdit_y_coord_keyword)
        self.verticalLayout.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label_10 = QtWidgets.QLabel(parent=self.tab_2)
        self.label_10.setMinimumSize(QtCore.QSize(150, 0))
        self.label_10.setMaximumSize(QtCore.QSize(150, 16777215))
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_12.addWidget(self.label_10)
        self.lineEdit_bin_keyword = QtWidgets.QLineEdit(parent=self.tab_2)
        self.lineEdit_bin_keyword.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.lineEdit_bin_keyword.setObjectName("lineEdit_bin_keyword")
        self.horizontalLayout_12.addWidget(self.lineEdit_bin_keyword)
        self.verticalLayout.addLayout(self.horizontalLayout_12)
        self.label_show_image = QtWidgets.QLabel(parent=self.tab_2)
        self.label_show_image.setMinimumSize(QtCore.QSize(0, 200))
        self.label_show_image.setText("")
        self.label_show_image.setObjectName("label_show_image")
        self.verticalLayout.addWidget(self.label_show_image)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.gridLayout_5.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 900, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "INK File Converter"))
        self.pushButton_open_folder.setText(_translate("MainWindow", "Open Folder"))
        self.pushButton_save_file_path.setText(_translate("MainWindow", "Save Path"))
        self.label.setText(_translate("MainWindow", "GOOD DIE: ----->"))
        self.lineEdit_good_die_output.setText(_translate("MainWindow", "1"))
        self.lineEdit_good_die_output.setPlaceholderText(_translate("MainWindow", "Map value"))
        self.label_2.setText(_translate("MainWindow", "FAILE DIE: ----->"))
        self.lineEdit_fail_die_output.setText(_translate("MainWindow", "X"))
        self.lineEdit_fail_die_output.setPlaceholderText(_translate("MainWindow", "Map value"))
        self.label_11.setText(_translate("MainWindow", "Emty Space: ---->"))
        self.lineEdit_empty_output.setText(_translate("MainWindow", "."))
        self.lineEdit_empty_output.setPlaceholderText(_translate("MainWindow", "Map value"))
        self.label_12.setText(_translate("MainWindow", "Good Die List: "))
        self.lineEdit_good_die_list.setToolTip(_translate("MainWindow", "use \',\' to split"))
        self.lineEdit_good_die_list.setText(_translate("MainWindow", "0001"))
        self.lineEdit_good_die_list.setPlaceholderText(_translate("MainWindow", "Map value"))
        self.groupBox.setTitle(_translate("MainWindow", "Input File List"))
        self.pushButton_convert_file.setText(_translate("MainWindow", "Convert File"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Preview"))
        self.label_3.setText(_translate("MainWindow", "Lot ID:"))
        self.checkBox_extract_root_lot_id.setToolTip(_translate("MainWindow", "Extract Root Lot ID uncheck will extract lot id"))
        self.checkBox_extract_root_lot_id.setText(_translate("MainWindow", "Extract Root Lot ID         "))
        self.label_4.setText(_translate("MainWindow", "Wafer ID:"))
        self.checkBox_extract_wafer_id.setToolTip(_translate("MainWindow", "Extract Root Lot ID uncheck will extract lot id"))
        self.checkBox_extract_wafer_id.setText(_translate("MainWindow", "Remove \'W\' on WaferID"))
        self.label_5.setText(_translate("MainWindow", "Lot Wafer Location:"))
        self.label_6.setText(_translate("MainWindow", "Part ID Location:"))
        self.spinBox_part_id_location.setToolTip(_translate("MainWindow", "row number where the part id located"))
        self.label_7.setText(_translate("MainWindow", "FLAT:"))
        self.label_8.setText(_translate("MainWindow", "X Coordinate Keyword:"))
        self.lineEdit_x_coord_keyword.setText(_translate("MainWindow", "X="))
        self.label_9.setText(_translate("MainWindow", "Y Coordinate Keyword:"))
        self.lineEdit_y_coord_keyword.setText(_translate("MainWindow", "Y="))
        self.label_10.setText(_translate("MainWindow", "Bin Keyword:"))
        self.lineEdit_bin_keyword.setText(_translate("MainWindow", "B="))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Setting"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())


```python
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStatusBar,
    QDialog,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QGridLayout,
    QDialogButtonBox,
    QMessageBox,
    QFileDialog,
    QListWidgetItem
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, QCoreApplication, QPoint, QSize, QSettings
# from qt_material import apply_stylesheet
import qdarktheme
import sys
import pandas as pd 
import numpy as np 
import os

from MainWindow import Ui_MainWindow

class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.load_styles()
        self.setup_connections()
        self.save_file_path = ""
        self.select_file_path_list = {}

    # def load_styles(self):
    #     """Load QSS style file"""
    #     try:
    #         # Get current file directory
    #         current_dir = os.path.dirname(os.path.abspath(__file__))
    #         style_file = os.path.join(current_dir, "styles.qss")
            
    #         if os.path.exists(style_file):
    #             with open(style_file, 'r', encoding='utf-8') as f:
    #                 style_sheet = f.read()
    #             self.setStyleSheet(style_sheet)
    #             print(f"Style file loaded successfully: {style_file}")
    #         else:
    #             print(f"Style file not found: {style_file}")
    #     except Exception as e:
    #         print(f"Error loading style file: {e}")

    def setup_connections(self):
        """Setup button connections and event handlers"""
        # Connect Open Folder button to file dialog
        self.pushButton_open_folder.clicked.connect(self.open_file_dialog)
        
        # Connect Save Path button to save dialog
        self.pushButton_save_file_path.clicked.connect(self.open_save_dialog)
        
        # Connect Convert File button to conversion function
        self.pushButton_convert_file.clicked.connect(self.convert_files)

    def open_file_dialog(self):
        """Open system file dialog to select multiple files"""
        try:
            options = QFileDialog.Options()
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files",
                "",  # Start from current directory
                "All Files (*);;Text Files (*.txt);;CSV Files (*.csv);;Python Files (*.py);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;PDF Files (*.pdf)",
                options=options
            )
                
            if file_paths:
                print(f"Selected {len(file_paths)} files:")
                for file_path in file_paths:
                    print(f"  - {file_path}")
                
                # Store absolute file paths with filename as key
                self.select_file_path_list = {os.path.basename(file_path): os.path.abspath(file_path) for file_path in file_paths}
                
                # Display files in listView widget
                self.display_files_in_listview()
                
                # Show summary message
                QMessageBox.information(
                    self,
                    "Files Selected",
                    f"Successfully selected {len(file_paths)} files.\nFiles are now displayed in the list below."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening file dialog: {str(e)}")


    def display_files_in_listview(self):
        """Display selected files in the listWidget widget"""
        try:
            # Clear the existing list
            self.listWidget_file_list.clear()
            
            if not self.select_file_path_list:
                return
            
            # Add each file to the listWidget
            for filename, file_path in self.select_file_path_list.items():
                # Create list item with just filename
                item = QListWidgetItem(filename)
                # Store full path as item data for later use
                item.setData(Qt.UserRole, file_path)
                
                # Add to listWidget
                self.listWidget_file_list.addItem(item)
            
            print(f"Displayed {len(self.select_file_path_list)} files in listWidget")
            
        except Exception as e:
            print(f"Error displaying files in listWidget: {e}")
            QMessageBox.critical(self, "Error", f"Error displaying files: {str(e)}")


    def open_save_dialog(self):
        """Open system file dialog to select save location"""
        try:
            # Open save file dialog
            self.save_file_path = QFileDialog.getExistingDirectory(
                self,
                "Save File",
            )
            
            if self.save_file_path:
                print(f"Selected save path: {self.save_file_path}")
                # Update the save path line edit if needed
                self.lineEdit_save_file_path.setText(self.save_file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening save dialog: {str(e)}")
    
    def convert_files(self):
        """Convert selected files to the save location"""
        try:
            input_dict = {
                "good_die_output": self.lineEdit_good_die_output.text(),
                "fail_die_output": self.lineEdit_fail_die_output.text(),
                "empty_output": self.lineEdit_empty_output.text(),
                "good_die_list": self.lineEdit_good_die_list.text().split(","),
                "extract_root_lot_id": self.checkBox_extract_root_lot_id.isChecked(),
                "clean_wafer_id": self.checkBox_extract_wafer_id.isChecked(),
                "lot_wafer_location": self.spinBox_lot_wafer_location.value(),
                "part_id_location": self.spinBox_part_id_location.value(),
                "flat": self.spinBox_flat.value(),
                "x_coord_keyword": self.lineEdit_x_coord_keyword.text(),
                "y_coord_keyword": self.lineEdit_y_coord_keyword.text(),
                "bin_keyword": self.lineEdit_bin_keyword.text(),
            }
            print(input_dict)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error converting files: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # qdarktheme.setup_theme("light", corner_shape="sharp")
    window = App()
    # apply_stylesheet(app, theme="light_lightgreen.xml")
    window.show()
    sys.exit(app.exec())


```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from collections.abc import Mapping

def _to_rgb(color):
    """Accept '#RRGGBB' or (r,g,b) and return an RGBColor."""
    if color is None:
        return None
    if isinstance(color, tuple) and len(color) == 3:
        r, g, b = color
        return RGBColor(int(r), int(g), int(b))
    if isinstance(color, str):
        s = color.strip().lstrip("#")
        if len(s) == 6:
            return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    raise ValueError("Color must be '#RRGGBB' or (r,g,b).")

def add_table_from_dict(
    slide,
    data: Mapping[str, list],
    rows: int | None = None,
    cols: int | None = None,
    *,
    # placement & sizing
    left=Inches(1),
    top=Inches(1),
    width=Inches(8),
    height=Inches(1.5),
    col_widths: list | None = None,   # list of lengths (e.g., [Inches(2), Inches(1.5), ...])
    row_height=None,                  # Pt or Inches; single value or list per row
    # header & text
    header=True,
    font_size=Pt(12),
    align=PP_ALIGN.CENTER,
    # colors
    header_fill="#E8EEF9",
    body_fill="#FFFFFF",
    header_font_color="#000000",
    body_font_color="#000000",
):
    """
    Add a table to a slide using dict {column_name: [values...]} with styling controls.
    """
    if not isinstance(data, Mapping) or not data:
        raise ValueError("`data` must be a non-empty dict-like mapping.")

    col_names = list(data.keys())
    inferred_cols = len(col_names)
    max_len = max(len(v) for v in data.values())

    cols = inferred_cols if cols is None else cols
    if cols < inferred_cols:
        raise ValueError(f"cols={cols} smaller than number of data columns ({inferred_cols}).")

    inferred_rows = max_len + (1 if header else 0)
    rows = inferred_rows if rows is None else rows
    if rows < (1 if header else 0):
        raise ValueError("rows too small (must allow for header if header=True).")

    # create table
    shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = shape.table

    # set column widths
    if col_widths is not None:
        if len(col_widths) != cols:
            raise ValueError("Length of col_widths must equal number of columns.")
        for j, w in enumerate(col_widths):
            table.columns[j].width = w
    else:
        even = width / cols
        for j in range(cols):
            table.columns[j].width = even

    # set row height(s)
    if row_height is not None:
        if isinstance(row_height, (list, tuple)):
            if len(row_height) != rows:
                raise ValueError("If row_height is a list, it must have one entry per row.")
            for i, h in enumerate(row_height):
                table.rows[i].height = h
        else:
            for i in range(rows):
                table.rows[i].height = row_height

    # colors
    hdr_fill_rgb = _to_rgb(header_fill)
    body_fill_rgb = _to_rgb(body_fill)
    hdr_font_rgb = _to_rgb(header_font_color)
    body_font_rgb = _to_rgb(body_font_color)

    data_col_count = min(cols, inferred_cols)
    start_row = 0

    # header row
    if header:
        for j in range(data_col_count):
            cell = table.cell(0, j)
            cell.text = str(col_names[j])
            # fill
            if hdr_fill_rgb:
                cell.fill.solid()
                cell.fill.fore_color.rgb = hdr_fill_rgb
            # align + font
            tf = cell.text_frame
            p = tf.paragraphs[0]
            p.alignment = align
            if p.runs:
                for run in p.runs:
                    run.font.size = font_size
                    if hdr_font_rgb:
                        run.font.color.rgb = hdr_font_rgb
        start_row = 1

    # body cells
    body_rows_allowed = rows - start_row
    for j in range(data_col_count):
        col_vals = list(data[col_names[j]])
        # pad/truncate
        if len(col_vals) < body_rows_allowed:
            col_vals += [""] * (body_rows_allowed - len(col_vals))
        else:
            col_vals = col_vals[:body_rows_allowed]

        for i, val in enumerate(col_vals, start=start_row):
            cell = table.cell(i, j)
            cell.text = "" if val is None else str(val)
            # fill
            if body_fill_rgb:
                cell.fill.solid()
                cell.fill.fore_color.rgb = body_fill_rgb
            # align + font
            tf = cell.text_frame
            p = tf.paragraphs[0]
            p.alignment = align
            if p.runs:
                for run in p.runs:
                    run.font.size = font_size
                    if body_font_rgb:
                        run.font.color.rgb = body_font_rgb

    return table

# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank

    data = {
        "Name": ["Alice", "Bob", "Carol", "Dave"],
        "Score": [92, 85, 88, 90],
        "Passed": ["Yes", "Yes", "Yes", "Yes"],
    }

    table = add_table_from_dict(
        slide,
        data,
        rows=None, cols=None,                    # infer size
        left=Inches(0.8), top=Inches(1.3),      # position
        width=Inches(8.5), height=Inches(1.8),  # total size (affects default col widths)
        col_widths=[Inches(3), Inches(2.5), Inches(3)],  # per-column widths
        row_height=Inches(0.4),                 # fixed height for every row
        header=True,
        font_size=Pt(12),
        align=PP_ALIGN.CENTER,
        header_fill="#DDE8FF",
        body_fill=(255, 255, 255),
        header_font_color="#0F2A5F",
        body_font_color="#222222",
    )

    prs.save("styled_table.pptx")
    print("Saved styled_table.pptx")


from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def _to_rgb(color):
    """Accept '#RRGGBB' or (r,g,b) and return an RGBColor."""
    if color is None:
        return None
    if isinstance(color, tuple) and len(color) == 3:
        r, g, b = color
        return RGBColor(int(r), int(g), int(b))
    if isinstance(color, str):
        s = color.strip().lstrip("#")
        if len(s) == 6:
            return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    raise ValueError("Color must be '#RRGGBB' or (r,g,b).")

def add_rectangle(
    slide,
    text: str,
    left,
    top,
    width,
    height,
    font_size=Pt(14),
    font_color="#000000",
    font_name="Arial",
    background_color="#FFFFFF"
):
    """
    Add a rectangle shape with styled text.

    Args:
        slide: Slide object to add the shape on.
        text (str): Text to display in the rectangle.
        left, top, width, height: Position & size (use Inches() or Pt()).
        font_size: Font size (default 14pt).
        font_color: Font color ('#RRGGBB' or (r,g,b)).
        font_name: Font name (string).
        background_color: Fill color ('#RRGGBB' or (r,g,b)).

    Returns:
        shape: The rectangle shape object.
    """
    # add rectangle shape
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)

    # background color
    bg_rgb = _to_rgb(background_color)
    if bg_rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_rgb

    # remove default border line
    shape.line.fill.background()

    # text setup
    text_frame = shape.text_frame
    text_frame.clear()  # remove default empty paragraph
    p = text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text

    # font style
    run.font.size = font_size
    run.font.name = font_name
    fg_rgb = _to_rgb(font_color)
    if fg_rgb:
        run.font.color.rgb = fg_rgb

    return shape

# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank layout

    add_rectangle(
        slide,
        text="Hello World",
        left=Inches(1),
        top=Inches(1),
        width=Inches(3),
        height=Inches(1),
        font_size=Pt(18),
        font_color="#FFFFFF",
        font_name="Calibri",
        background_color="#2E86DE"
    )

    prs.save("rectangle_example.pptx")
    print("Saved rectangle_example.pptx")


```Python
# pip install duckdb pandas
import duckdb
import pandas as pd

DB_PATH = "spc.duckdb"
con = duckdb.connect(DB_PATH)

# Create table (note: "value" is quoted because it's a common identifier)
con.execute("""
CREATE TABLE IF NOT EXISTS spc_records (
    id BIGINT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    root_lot_id VARCHAR NOT NULL,
    wafer_id VARCHAR NOT NULL,
    metro_tkout_time TIMESTAMP,
    metro_eqp_id VARCHAR,
    metro_item_id VARCHAR NOT NULL,
    "value" DOUBLE,
    subitem_id VARCHAR,
    target DOUBLE,
    spec_high DOUBLE,
    spec_low DOUBLE,
    ucl DOUBLE,
    lcl DOUBLE,
    area VARCHAR,
    grade VARCHAR,
    std_ooc_fail BOOLEAN,
    oos_fail BOOLEAN,
    ooc_fail BOOLEAN,
    site_ooc_fail BOOLEAN,
    metro_step_description VARCHAR NOT NULL,
    metro_step_seq VARCHAR NOT NULL
);
""")

# Enforce “do-not-duplicate” with a UNIQUE index on your chosen key
con.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS uniq_spc_key
ON spc_records (root_lot_id, wafer_id, metro_step_seq, metro_item_id, COALESCE(subitem_id, ''));
""")

def insert_spc_dataframe(con: duckdb.DuckDBPyConnection, df: pd.DataFrame):
    """
    Insert only NEW rows from `df` (which must have all columns except `id`).
    A row is considered new if no existing row shares the same:
      (root_lot_id, wafer_id, metro_step_seq, metro_item_id, subitem_id)
    """
    required_cols = [
        "root_lot_id", "wafer_id", "metro_tkout_time", "metro_eqp_id",
        "metro_item_id", "value", "subitem_id", "target", "spec_high",
        "spec_low", "ucl", "lcl", "area", "grade", "std_ooc_fail", "oos_fail",
        "ooc_fail", "site_ooc_fail", "metro_step_description", "metro_step_seq"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    con.register("staging_df", df)

    con.execute("""
        MERGE INTO spc_records AS t
        USING (
            SELECT
                root_lot_id,
                wafer_id,
                CAST(metro_tkout_time AS TIMESTAMP) AS metro_tkout_time,
                metro_eqp_id,
                metro_item_id,
                "value",
                subitem_id,
                target,
                spec_high,
                spec_low,
                ucl,
                lcl,
                area,
                grade,
                std_ooc_fail,
                oos_fail,
                ooc_fail,
                site_ooc_fail,
                metro_step_description,
                metro_step_seq
            FROM staging_df
        ) AS s
        ON  t.root_lot_id = s.root_lot_id
        AND t.wafer_id    = s.wafer_id
        AND t.metro_step_seq = s.metro_step_seq
        AND t.metro_item_id  = s.metro_item_id
        AND COALESCE(t.subitem_id, '') = COALESCE(s.subitem_id, '')
        WHEN NOT MATCHED THEN INSERT (
            root_lot_id, wafer_id, metro_tkout_time, metro_eqp_id, metro_item_id,
            "value", subitem_id, target, spec_high, spec_low, ucl, lcl,
            area, grade, std_ooc_fail, oos_fail, ooc_fail, site_ooc_fail,
            metro_step_description, metro_step_seq
        ) VALUES (
            s.root_lot_id, s.wafer_id, s.metro_tkout_time, s.metro_eqp_id, s.metro_item_id,
            s."value", s.subitem_id, s.target, s.spec_high, s.spec_low, s.ucl, s.lcl,
            s.area, s.grade, s.std_ooc_fail, s.oos_fail, s.ooc_fail, s.site_ooc_fail,
            s.metro_step_description, s.metro_step_seq
        );
    """)
    con.unregister("staging_df")


# --- Example usage ---
# df = pd.DataFrame([...]) # build a dataframe without `id`
# insert_spc_dataframe(con, df)
# con.close()




import pandas as pd
import numpy as np

# ---- Function under test (same as I gave you) ----
def pivot_wafers_with_flags(
    df,
    n_wafers=25,
    lot_col="root_lot_id",
    item_col="metro_item_id",
    step_col="metro_step_seq",
    wafer_col="wafer_id",
    value_col="fab_value",
    oos_col="oos_fail",
    ooc_col="ooc_fail",
    std_col="std_ooc_fail",
    site_oos_col="site_oos_fail",
):
    df = df.copy()

    def norm_w(w):
        w = str(w).strip().upper()
        if w.startswith("W"):
            num = w[1:]
            if num.isdigit():
                return f"W{int(num):02d}"
        return w

    df[wafer_col] = df[wafer_col].map(norm_w)

    # Coerce TRUE/FALSE strings to booleans if necessary
    for c in [oos_col, ooc_col, std_col, site_oos_col]:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.upper().map({"TRUE": True, "FALSE": False}).fillna(df[c])

    def row_flag(r):
        if bool(r[oos_col]): return 1
        if bool(r[ooc_col]): return 2
        if bool(r[std_col]): return 3
        if bool(r[site_oos_col]): return 4
        return 0

    df["flag_code"] = df.apply(row_flag, axis=1).astype(int)

    group_cols = [lot_col, item_col, step_col]
    all_wafers = [f"W{i:02d}" for i in range(1, n_wafers + 1)]

    # Pivot values (mean for duplicates)
    pv_val = (
        pd.pivot_table(
            df, index=group_cols, columns=wafer_col, values=value_col, aggfunc="mean"
        )
        .reindex(columns=all_wafers)
        .sort_index()
    )

    # Pivot flags (min => highest severity code since 1 is most severe)
    pv_flag = (
        pd.pivot_table(
            df, index=group_cols, columns=wafer_col, values="flag_code", aggfunc="min"
        )
        .reindex(columns=all_wafers)
        .fillna(0)
        .astype(int)
        .sort_index()
    )
    pv_flag.columns = [f"F{c[1:]}" for c in pv_flag.columns]

    out = pd.concat([pv_val, pv_flag], axis=1).reset_index()

    # Order columns
    w_cols = all_wafers
    f_cols = [f"F{i:02d}" for i in range(1, n_wafers + 1)]
    out = out[group_cols + w_cols + f_cols]
    return out
