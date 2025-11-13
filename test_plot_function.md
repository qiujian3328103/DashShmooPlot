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
