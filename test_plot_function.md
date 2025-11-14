```python
from __future__ import annotations

import dash
import pandas as pd
from typing import Optional, List
from dash import html, Input, Output
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
import feffery_antd_charts as fact

app = dash.Dash(__name__)

# =========================
# Load data
# =========================
df = pd.read_excel(r"C:\Users\Jian Qiu\Downloads\test_data1.xlsx")

# =========================
# Palette & helpers
# =========================
_PALETTE = [
    "#5B8FF9", "#5AD8A6", "#5D7092", "#F6BD16", "#E8684A",
    "#6DC8EC", "#9270CA", "#FF9D4D", "#269A99", "#FF99C3",
    "#BBDEFB", "#C5E1A5", "#B39DDB", "#FFE082", "#EF9A9A"
]

CONTROL_COLOR = "#fadb14"   # UCL/LCL
USL_COLOR     = "#ff4d4f"   # USL (also used for OOS marker ring)
LSL_COLOR     = "#722ed1"   # LSL
TARGET_COLOR  = "#595959"   # Target

def _color_for_key(key: str) -> str:
    s, h = str(key), 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return _PALETTE[h % len(_PALETTE)]

def compute_spec_defaults(y_series, usl=None, lsl=None, pad_ratio=0.10, pad_min=0.05):
    """Compute default Y axis limits centered around spec window (LSL..USL) with padding."""
    y_series = y_series.dropna()
    data_min = float(y_series.min()) if not y_series.empty else 0.0
    data_max = float(y_series.max()) if not y_series.empty else 1.0

    base_lo = float(lsl) if lsl is not None else data_min
    base_hi = float(usl) if usl is not None else data_max
    if base_hi < base_lo:
        base_lo, base_hi = base_hi, base_lo

    span = max(1e-9, base_hi - base_lo)
    pad = max(pad_min, span * pad_ratio)

    def_lo = base_lo - pad
    def_hi = base_hi + pad
    rail_lo = def_lo - pad
    rail_hi = def_hi + pad

    return {
        "def_lo": def_lo, "def_hi": def_hi,
        "rail_lo": rail_lo, "rail_hi": rail_hi
    }

# =========================
# Chart factory
# =========================
def make_spc_line(
    df: pd.DataFrame,
    x: str,
    y: str,
    *,
    group_by: Optional[str] = None,       # color points by this, but keep a single line
    # limits
    ucl: Optional[float] = None,
    lcl: Optional[float] = None,
    usl: Optional[float] = None,
    lsl: Optional[float] = None,
    target: Optional[float] = None,
    accept: Optional[float] = None,       # optional band ±accept around target
    # colors
    control_color: str = CONTROL_COLOR,
    usl_color: str = USL_COLOR,
    lsl_color: str = LSL_COLOR,
    target_color: str = TARGET_COLOR,
    line_color: str = "#262626",
    point_size: float = 6.0,
    # SPC horizontal zones
    show_spc_zone: bool = True,
    zone_green: str = "#d9f7be",          # [LCL, UCL]
    zone_yellow: str = "#fff1b8",         # (UCL, USL] and [LSL, LCL)
    zone_red: str = "#ffccc7",            # >USL or <LSL
    zone_opacity: float = 0.35,
    # annotation labels off by default
    show_line_labels: bool = False,
    show_marker_labels: bool = False,
    # chart UX
    height: int = 520,
    auto_fit: bool = True,
    smooth: bool = False,
    show_slider: bool = True,
    slider_height: int = 30,
    # initial y-range (if provided, overrides 'nice')
    initial_y_min: Optional[float] = None,
    initial_y_max: Optional[float] = None,
    # id for callbacks
    chart_id: str = "spc-line",
) -> fact.AntdLine:

    need_cols = [x, y] + ([group_by] if group_by else [])
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    work = df.copy()

    # ---------- X handling ----------
    x_is_dt = pd.api.types.is_datetime64_any_dtype(work[x])
    if not x_is_dt:
        try:
            work[x] = pd.to_datetime(work[x], errors="raise")
            x_is_dt = True
        except Exception:
            x_is_dt = False

    use_index_x = False
    if x_is_dt:
        work.sort_values(by=[x], inplace=True, kind="mergesort")
        work["_x_plot"] = pd.to_datetime(work[x]).dt.strftime("%Y-%m-%d %H:%M:%S")
        x_field = "_x_plot"
        x_meta = {"type": "timeCat", "alias": x, "nice": True}
    else:
        if "tkout_time" not in work.columns:
            raise ValueError("x is not datetime and 'tkout_time' is required for secondary sort.")
        if not pd.api.types.is_datetime64_any_dtype(work["tkout_time"]):
            work["tkout_time"] = pd.to_datetime(work["tkout_time"], errors="raise")
        work.sort_values(by=["tkout_time"], inplace=True, kind="mergesort")
        work["_x_idx"] = range(len(work))
        use_index_x = True
        x_field = "_x_idx"
        x_meta = {"type": "linear", "alias": "Index", "nice": True}

    # ---------- Chart data ----------
    keep_cols: List[str] = [
        "root_lot_id", "wafer_id", "part_id", "process_id",
        "eqp_id", "lot_type", y, x_field
    ]
    keep_cols = [c for c in keep_cols if c in work.columns]
    chart_data = work[keep_cols].rename(columns={x_field: "x"}).to_dict("records")

    # ---------- Annotations ----------
    def hline(val: float, label: str, color: str, dash: bool = False, width: float = 1.0):
        ann = {
            "type": "line",
            "start": ["min", val],
            "end": ["max", val],
            "style": {"stroke": color, "lineWidth": width, "lineDash": [4, 4] if dash else None}
        }
        if show_line_labels:
            ann["text"] = {"content": label, "position": "end", "style": {"fill": color}}
        return ann

    annotations = []
    # spec/control/target lines
    if usl is not None: annotations.append(hline(usl, f"USL = {usl:g}", usl_color))
    if lsl is not None: annotations.append(hline(lsl, f"LSL = {lsl:g}", lsl_color, dash=True))
    if ucl is not None: annotations.append(hline(ucl, f"UCL = {ucl:g}", control_color))
    if lcl is not None: annotations.append(hline(lcl, f"LCL = {lcl:g}", control_color))
    if target is not None: annotations.append(hline(target, f"Target = {target:g}", TARGET_COLOR))

    # optional accept band around target
    if target is not None and accept is not None and accept >= 0:
        annotations.append({
            "type": "region",
            "start": ["min", target - accept],
            "end":   ["max", target + accept],
            "style": {"fill": "#e6fffb", "fillOpacity": 0.25, "opacity": 1}
        })

    # SPC horizontal zones
    if show_spc_zone:
        if lcl is not None and ucl is not None and lcl < ucl:
            annotations.append({
                "type": "region",
                "start": ["min", lcl],
                "end":   ["max", ucl],
                "style": {"fill": zone_green, "fillOpacity": zone_opacity, "opacity": 1}
            })
        if ucl is not None and usl is not None and ucl < usl:
            annotations.append({
                "type": "region",
                "start": ["min", ucl],
                "end":   ["max", usl],
                "style": {"fill": zone_yellow, "fillOpacity": zone_opacity, "opacity": 1}
            })
        if lsl is not None and lcl is not None and lsl < lcl:
            annotations.append({
                "type": "region",
                "start": ["min", lsl],
                "end":   ["max", lcl],
                "style": {"fill": zone_yellow, "fillOpacity": zone_opacity, "opacity": 1}
            })
        if usl is not None:
            annotations.append({
                "type": "region",
                "start": ["min", usl],
                "end":   ["max", "max"],
                "style": {"fill": zone_red, "fillOpacity": zone_opacity, "opacity": 1}
            })
        if lsl is not None:
            annotations.append({
                "type": "region",
                "start": ["min", "min"],
                "end":   ["max", lsl],
                "style": {"fill": zone_red, "fillOpacity": zone_opacity, "opacity": 1}
            })

    # Out-of-spec markers (no label)
    if usl is not None or lsl is not None:
        for row in work.itertuples(index=False):
            yv = getattr(row, y)
            xv = getattr(row, "_x_idx", None) if use_index_x else getattr(row, "_x_plot", None)
            if xv is None:
                continue
            is_high = (usl is not None and yv > usl)
            is_low  = (lsl is not None and yv < lsl)
            if is_high or is_low:
                dm = {
                    "type": "dataMarker",
                    "position": {"x": xv if use_index_x else str(xv), "y": float(yv)},
                    "point": {"style": {"stroke": usl_color, "fill": "#fff", "r": point_size + 1, "lineWidth": 2}},
                    "direction": "upward" if is_high else "downward"
                }
                if show_marker_labels:
                    dm["text"] = {"content": "OOS", "style": {"fill": "#000"}}
                annotations.append(dm)

    # ---------- Series & styles ----------
    series_field = None                            # single line
    lineStyle = {"stroke": line_color, "lineWidth": 2}

    # color points by group
    if group_by:
        point_color = {
            "func": f"""
            (d) => {{
                const palette = { _PALETTE };
                const key = d?.{group_by} ?? "default";
                let h = 0;
                for (let i = 0; i < String(key).length; i++) {{
                    h = (h * 31 + String(key).charCodeAt(i)) >>> 0;
                }}
                return palette[h % palette.length];
            }}
            """
        }
    else:
        point_color = line_color

    # initial y-axis bounds if provided
    y_axis_cfg = {"title": {"text": y}, "nice": True}
    if initial_y_min is not None and initial_y_max is not None:
        y_axis_cfg = {"title": {"text": y}, "min": float(initial_y_min), "max": float(initial_y_max), "nice": False}

    # tooltip shows everything you fed in
    tooltip_fields = list(chart_data[0].keys()) if chart_data else ["x", y]
    if "x" not in tooltip_fields:
        tooltip_fields.insert(0, "x")

    slider = {"start": 0.0, "end": 1.0, "height": slider_height} if show_slider else False
    meta = {"x": x_meta, y: {"alias": y, "nice": True}}

    return fact.AntdLine(
        id=chart_id,
        data=chart_data,
        xField="x",
        yField=y,
        seriesField=series_field,
        connectNulls=True,
        smooth=smooth,
        autoFit=auto_fit,
        lineStyle=lineStyle,
        point={"color": point_color, "style": {"r": point_size, "stroke": "black"}},
        color=line_color,
        xAxis={"title": {"text": "Index" if use_index_x else x}, "nice": True, "label": {"autoRotate": True}},
        yAxis=y_axis_cfg,
        legend=False,  # boolean to avoid version issues
        tooltip={"showTitle": False, "fields": tooltip_fields},
        meta=meta,
        slider=slider,
        annotations=annotations,
        height=height,
        style={"padding": "50px 100px"}
    )

# =========================
# Build component + Y slider (spec-aware defaults)
# =========================
USL_VAL, LSL_VAL = 5.0, 0.0   # set your specs here (keep in sync with chart call)
y_info = compute_spec_defaults(df["fab_value"], usl=USL_VAL, lsl=LSL_VAL, pad_ratio=0.10, pad_min=0.02)
Y_DEF_LO, Y_DEF_HI = y_info["def_lo"], y_info["def_hi"]
Y_RAIL_LO, Y_RAIL_HI = y_info["rail_lo"], y_info["rail_hi"]

spc = make_spc_line(
    df,
    x="tkout_time",
    y="fab_value",
    group_by="part_id",
    usl=USL_VAL, lsl=LSL_VAL, ucl=0.5, lcl=0.1, target=0.25, accept=0.05,
    show_spc_zone=True,
    initial_y_min=Y_DEF_LO,
    initial_y_max=Y_DEF_HI
)

app.layout = html.Div(
    [
        fac.AntdSpace(
            [
                fac.AntdText("Y-axis range:"),
                fac.AntdSlider(
                    id="y-range",
                    range=True,
                    min=Y_RAIL_LO,
                    max=Y_RAIL_HI,
                    step=(Y_RAIL_HI - Y_RAIL_LO) / 200 if Y_RAIL_HI > Y_RAIL_LO else 0.01,
                    defaultValue=[Y_DEF_LO, Y_DEF_HI],
                    style={"width": 520}
                ),
                fac.AntdButton("Reset Y", id="y-reset")
            ],
            align="center",
            size="small",
            wrap=True,
            style={"marginBottom": 12}
        ),
        spc
    ],
    style=style(padding=50),
)

# =========================
# Callback: slider -> yAxis
# =========================
@app.callback(
    Output("spc-line", "yAxis"),
    Input("y-range", "value"),
    Input("y-reset", "nClicks"),
    prevent_initial_call=False
)
def update_yaxis(y_range, reset_clicks):
    ctx = dash.callback_context
    # Reset to spec-aware defaults
    if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("y-reset"):
        return {"title": {"text": "fab_value"}, "min": Y_DEF_LO, "max": Y_DEF_HI, "nice": False}

    if not y_range or len(y_range) != 2:
        return {"title": {"text": "fab_value"}, "min": Y_DEF_LO, "max": Y_DEF_HI, "nice": False}

    lo, hi = sorted([float(y_range[0]), float(y_range[1])])
    if hi - lo < 1e-6:
        mid = (hi + lo) / 2.0
        lo, hi = mid - 0.0005, mid + 0.0005
    return {"title": {"text": "fab_value"}, "min": lo, "max": hi, "nice": False}

# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(debug=True)
```


```python
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from plotly.colors import qualitative
from typing import Optional

palette_name = "plotly"
COLOR_PALETTE = getattr(qualitative, palette_name, qualitative.Set3)


def plot_spec(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp',
    value_col: str = 'value',
    group_col: str = None,
    x_col: str = None,
    usl: Optional[float] = None,
    lsl: Optional[float] = None,
    ucl: Optional[float] = None,
    lcl: Optional[float] = None,
    target: Optional[float] = None,
    auto_limits: bool = True,
    show_annotations: bool = True,
    show_zones: bool = True,
    show_rangeslider: bool = True,
):
    df = df.copy()

    # --- basic validation ---
    required = {timestamp_col, value_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # sort and ensure datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df.sort_values(by=timestamp_col, inplace=True)

    # numeric x index (for spacing) – we hide tick labels anyway
    if x_col is not None and x_col in df.columns:
        df["__x_index__"] = df[x_col].astype(int)
    else:
        df["__x_index__"] = np.arange(len(df))

    # helper to convert limits safely
    def _to_float_or_none(x):
        return None if x is None else float(x)

    usl = _to_float_or_none(usl)
    lsl = _to_float_or_none(lsl)
    ucl = _to_float_or_none(ucl)
    lcl = _to_float_or_none(lcl)
    target = _to_float_or_none(target)

    # --- auto control limits (3-sigma around target) ---
    if auto_limits:
        if target is None:
            target = float(df[value_col].mean())
        sigma = float(df[value_col].std(ddof=1)) if len(df) > 1 else 0.0
        if sigma > 0:
            if lcl is None:
                lcl = target - 3 * sigma
            if ucl is None:
                ucl = target + 3 * sigma

    # --- violations (only if lcl & ucl exist) ---
    if lcl is not None and ucl is not None:
        viol_mask = (df[value_col] < lcl) | (df[value_col] > ucl)
    else:
        viol_mask = pd.Series(False, index=df.index)

    violations = df[viol_mask]

    # --- hover data ---
    raw_hover_cols = ['root_lot_id', 'wafer_id', 'tkout_time',
                      'fab_value', 'item_id', 'step_seq']
    hover_cols = [c for c in raw_hover_cols if c in df.columns]
    hover_template = ""
    for i, col in enumerate(hover_cols):
        hover_template += f"{col}: %{{customdata[{i}]}}<br>"
    hover_template = hover_template + f"{value_col}: %{{y}}<extra></extra>"

    # --- main data traces (grouped or not) ---
    traces = []

    if group_col and group_col in df.columns:
        group_values = df[group_col].unique()
        color_map = {
            g: COLOR_PALETTE[i % len(COLOR_PALETTE)]
            for i, g in enumerate(group_values)
        }

        for g in group_values:
            gdf = df[df[group_col] == g]
            custom_data = gdf[hover_cols].values if hover_cols else None

            traces.append(
                go.Scatter(
                    x=gdf["__x_index__"],
                    y=gdf[value_col],
                    mode='lines+markers',
                    name=str(g),
                    line=dict(color=color_map[g], width=2),
                    marker=dict(color=color_map[g], size=8, symbol='circle'),
                    customdata=custom_data,
                    hovertemplate=hover_template,
                )
            )
    else:
        custom_data = df[hover_cols].values if hover_cols else None
        traces.append(
            go.Scatter(
                x=df["__x_index__"],
                y=df[value_col],
                mode='lines+markers',
                name="Data",
                line=dict(color='black', width=2),
                marker=dict(size=8, symbol='circle'),
                customdata=custom_data,
                hovertemplate=hover_template,
            )
        )

    # violation markers (separate trace)
    if not violations.empty:
        traces.append(
            go.Scatter(
                x=violations["__x_index__"],
                y=violations[value_col],
                mode='markers',
                name="Violations",
                marker=dict(
                    color='red',
                    size=12,
                    symbol='circle-open',
                    opacity=0.7,
                ),
                hoverinfo='all',
            )
        )

    # --- x-range fix for single point ---
    xmin, xmax = df["__x_index__"].min(), df["__x_index__"].max()
    if xmin == xmax:
        xmin -= 0.5
        xmax += 0.5

    # --- compute nice y-range (spec centered) ---
    vals_for_range = [df[value_col].min(), df[value_col].max()]
    for v in [lsl, lcl, ucl, usl, target]:
        if v is not None and np.isfinite(v):
            vals_for_range.append(v)

    y_min = min(vals_for_range)
    y_max = max(vals_for_range)
    span = y_max - y_min if y_max > y_min else 1.0

    # choose center: prefer spec band, then target, then middle of data
    if (lsl is not None) and (usl is not None):
        center = (lsl + usl) / 2.0
    elif target is not None:
        center = target
    else:
        center = (y_min + y_max) / 2.0

    half = span * 0.6
    y_lower = min(y_min, center - half)
    y_upper = max(y_max, center + half)

    pad = 0.05 * span
    y_lower -= pad
    y_upper += pad

    # --- shapes for zones + horizontal lines ---
    shapes = []
    annotations = []

    # Per-region zones: only draw region if needed limits exist
    if show_zones:
        # below LSL -> red (requires LSL)
        if lsl is not None:
            shapes.append(
                dict(
                    type="rect",
                    xref="x", x0=xmin, x1=xmax,
                    yref="y", y0=y_lower, y1=lsl,
                    line=dict(width=0),
                    fillcolor='#ffccc7',    # red-ish
                    opacity=0.35,
                )
            )

        # between LSL and LCL -> yellow (requires both)
        if (lsl is not None) and (lcl is not None) and (lsl < lcl):
            shapes.append(
                dict(
                    type="rect",
                    xref="x", x0=xmin, x1=xmax,
                    yref="y", y0=lsl, y1=lcl,
                    line=dict(width=0),
                    fillcolor='#fff1b8',    # yellow-ish
                    opacity=0.35,
                )
            )

        # between LCL and UCL -> green (requires both)
        if (lcl is not None) and (ucl is not None) and (lcl < ucl):
            shapes.append(
                dict(
                    type="rect",
                    xref="x", x0=xmin, x1=xmax,
                    yref="y", y0=lcl, y1=ucl,
                    line=dict(width=0),
                    fillcolor='#cfead1',    # green-ish
                    opacity=0.35,
                )
            )

        # between UCL and USL -> yellow (requires both)
        if (ucl is not None) and (usl is not None) and (ucl < usl):
            shapes.append(
                dict(
                    type="rect",
                    xref="x", x0=xmin, x1=xmax,
                    yref="y", y0=ucl, y1=usl,
                    line=dict(width=0),
                    fillcolor='#fff1b8',    # yellow-ish
                    opacity=0.35,
                )
            )

        # above USL -> red (requires USL)
        if usl is not None:
            shapes.append(
                dict(
                    type="rect",
                    xref="x", x0=xmin, x1=xmax,
                    yref="y", y0=usl, y1=y_upper,
                    line=dict(width=0),
                    fillcolor='#ffccc7',    # red-ish
                    opacity=0.35,
                )
            )

    # helper: add "infinite" horizontal lines and optional annotations
    def add_limit_line_and_label(name, y, color, dash="dash", width=2, show_label=True):
        if y is None:
            return

        # horizontal line across full plot width
        shapes.append(
            dict(
                type="line",
                xref="paper", x0=0, x1=1,  # span full width of plot
                yref="y", y0=y, y1=y,
                line=dict(color=color, width=width, dash=dash),
            )
        )

        if not (show_annotations and show_label):
            return

        text = f"{name} = {y:.4g}"

        # annotation slightly inside the right edge of the plotting area
        annotations.append(
            dict(
                xref="paper",
                yref="y",
                x=0.99,          # a bit inside the right edge
                y=y,
                xanchor="right", # align text inside
                yanchor="middle",
                text=text,
                showarrow=False,
                font=dict(color=color, size=10),
                align="right",
                xshift=0,
                bgcolor="rgba(255,255,255,0.7)",
                bordercolor=color,
                borderwidth=0,
                borderpad=1,
            )
        )

    # control limits (blue dashed)
    add_limit_line_and_label("UCL", ucl, "#1890ff", dash="dash", width=2)
    add_limit_line_and_label("LCL", lcl, "#1890ff", dash="dash", width=2)

    # spec limits (red dashed)
    add_limit_line_and_label("USL", usl, "#ff4d4f", dash="dash", width=2)
    add_limit_line_and_label("LSL", lsl, "#ff4d4f", dash="dash", width=2)

    # target line (gray dotted)
    add_limit_line_and_label("Target", target, "#595959", dash="dot", width=1.5)

    # --- xaxis config (with optional rangeslider) ---
    xaxis = dict(
        title=None,
        zeroline=False,
        showticklabels=False,
        range=[xmin, xmax],
    )
    if show_rangeslider:
        xaxis["rangeslider"] = dict(visible=True)

    # --- layout ---
    layout = go.Layout(
        title=None,
        xaxis=xaxis,
        yaxis=dict(
            title=value_col,
            zeroline=False,
            range=[y_lower, y_upper],
        ),
        legend=dict(
            x=1.01, y=1,
            xanchor='right', yanchor='top',
            orientation='v',
            bgcolor="rgba(255, 255, 255, 0)",
            bordercolor="rgba(0, 0, 0, 0)",
            borderwidth=1
        ),
        hovermode='closest',
        margin=dict(l=0, r=10, t=25, b=0),  # small right margin
        shapes=shapes,
        annotations=annotations,
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig


if __name__ == "__main__":
    df = pd.read_excel(r"C:\\Users\\Jian Qiu\\Downloads\\test_data1.xlsx")
    fig = plot_spec(
        df,
        timestamp_col="tkout_time",
        value_col="fab_value",
        group_col="part_id",
        usl=2.0, lsl=0.0, target=0.25,
        lcl=0.1, ucl=0.5,
        auto_limits=True,
        show_zones=True,
        show_rangeslider=True,
        show_annotations=True,
    )
    fig.show()


```
