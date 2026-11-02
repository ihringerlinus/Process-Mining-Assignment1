import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from calendar import monthrange

from event_enricher import case_add_activity_start_time, convert_name


def performance_spectrum(case_log, event_log, source_activity, target_activity):
    source = convert_name(source_activity)
    target = convert_name(target_activity)
    for act in [source_activity, target_activity]:
        # if (act+'::start') not in case_log.columns:
        case_log = case_add_activity_start_time(case_log, event_log, act, time_col='rel_log_time')
    N = len(case_log)
    X = []
    for case_id in case_log.index[:N]:
        create_time = case_log.at[case_id, source+'::start']
        send_time = case_log.at[case_id, target+'::start']
        X.extend([create_time, send_time, None])

    Y = []
    for i in range(N):
        Y.extend([1, 0, None])

    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=X, y=Y, mode="lines", line=dict(width=1)))
    fig.update_yaxes(
        tickvals=[0, 1],          # the y-values you want to label
        ticktext=[target_activity, source_activity]  # the corresponding labels
    )
    fig.update_xaxes(title="Relative log time in days", rangeslider_visible=True)

    return fig


def calendar_heatmap(
    data,
    date_col=None,
    value_col=None,
    year=None,
    agg="sum",
    title=None,
    colorscale=None,          # None -> white->blue default
    showscale=True,
    value_format=".2f",
    fillna_value=0,           # <-- fill missing days
    row_spacing=0.12,         # <-- vertical spacing between rows
    log_scale=False,          # <-- NEW: use log1p for color mapping
):
    """
    Calendar heatmap (3x4 months) with optional log color mapping.
    - If log_scale=True, colors are based on log1p(values) but hover shows original values.
    """

    # ---- Normalize inputs to a daily series ----
    if isinstance(data, pd.Series):
        s = data.copy()
        if not isinstance(s.index, pd.DatetimeIndex):
            s.index = pd.to_datetime(s.index)
        s.name = s.name or "value"
    else:
        if date_col is None or value_col is None:
            raise ValueError("For DataFrame input, pass date_col= and value_col=.")
        df = data[[date_col, value_col]].copy()
        df[date_col] = pd.to_datetime(df[date_col])
        s = df.set_index(date_col)[value_col]

    # Pick a year if not specified: use the most frequent year in the index
    if year is None:
        if len(s) == 0:
            raise ValueError("No data to infer a year from.")
        years = pd.Series(s.index.year)
        year = int(years.mode().iat[0])

    # Keep only that year and aggregate by day
    s_year = s[(s.index.year == year)]
    if s_year.empty:
        # build an empty series so the grid still renders
        s_year = pd.Series(dtype=float)

    if agg not in {"sum", "mean", "max", "min"}:
        raise ValueError("agg must be one of: 'sum', 'mean', 'max', 'min'")
    daily = getattr(s_year.groupby(s_year.index.normalize()), agg)()

    # Ensure every day exists; fill missing with chosen value (often 0)
    all_days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    daily = daily.reindex(all_days).fillna(fillna_value)

    # Prepare the color values (z) and the original values for hover
    # Handle negatives safely when log-scaling by shifting if needed
    orig_vals = daily.astype(float).values
    if log_scale:
        min_val = np.nanmin(orig_vals) if orig_vals.size else 0.0
        if min_val < 0:
            # shift so the minimum is 0, then log1p
            shift = -min_val
            zvals = np.log1p(orig_vals + shift)
        else:
            # non-negative: use log1p directly
            zvals = np.log1p(orig_vals)
    else:
        zvals = orig_vals.copy()

    # For consistent color axis across months
    if np.isfinite(zvals).any():
        zmin = float(np.nanmin(zvals))
        zmax = float(np.nanmax(zvals))
        if zmin == zmax:
            zmin, zmax = zmin - 1.0, zmax + 1.0
    else:
        zmin, zmax = 0.0, 1.0

    # Default colorscale: pure white at 0 -> deep blue at max
    if colorscale is None:
        colorscale = [[0.0, "white"], [1.0, "#08519c"]]

    # Build 3x4 subplots
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fig = make_subplots(
        rows=3, cols=4,
        horizontal_spacing=0.03,
        vertical_spacing=row_spacing,   # <-- spacing control
        subplot_titles=[f"{month_names[m-1]}" for m in range(1, 13)]
    )

    weekday_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    # helper to format numbers in hover
    def fmt_num(x):
        try:
            return f"{x:{value_format}}"
        except Exception:
            return str(x)

    # Fill each month
    for m in range(1, 13):
        first_weekday, ndays = monthrange(year, m)  # Monday=0..Sunday=6

        # grids
        z = np.full((6, 7), np.nan, dtype=float)         # transformed values for color
        text = [["" for _ in range(7)] for _ in range(6)]
        custom = [[None for _ in range(7)] for _ in range(6)]  # [date_str, original_value, transformed_value]

        for day in range(1, ndays + 1):
            dt = pd.Timestamp(year=year, month=m, day=day)
            wday = dt.weekday()  # 0..6
            week_idx = (day + first_weekday - 1) // 7

            # index into our 1D arrays
            idx = (dt - all_days[0]).days
            orig = orig_vals[idx] if 0 <= idx < len(orig_vals) else np.nan
            zv = zvals[idx] if 0 <= idx < len(zvals) else np.nan

            z[week_idx, wday] = zv
            text[week_idx][wday] = str(day)
            custom[week_idx][wday] = [dt.strftime("%Y-%m-%d"), None if np.isnan(orig) else float(orig), None if np.isnan(zv) else float(zv)]

        r = (m - 1) // 4 + 1
        c = (m - 1) % 4 + 1

        fig.add_trace(
            go.Heatmap(
                z=z,
                x=weekday_labels,
                y=[f"W{i+1}" for i in range(6)],
                text=text,
                texttemplate="%{text}",
                textfont={"size": 10},
                customdata=custom,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Week: %{y} — %{x}<br>"
                    "Value: %{customdata[1]:" + value_format + "}"
                    + ( "<br>log1p(value): %{customdata[2]:.3f}" if log_scale else "" )
                    + "<extra></extra>"
                ),
                coloraxis="coloraxis",
                showscale=False,
                xgap=2, ygap=2,
            ),
            row=r, col=c
        )

        # Tidy axes
        fig.update_xaxes(
            tickmode="array", tickvals=weekday_labels, ticktext=weekday_labels,
            showgrid=False, zeroline=False, showline=False,
            row=r, col=c
        )
        fig.update_yaxes(
            tickmode="array",
            tickvals=[f"W{i+1}" for i in range(6)],
            ticktext=[f"W{i+1}" for i in range(6)],
            autorange="reversed", showgrid=False, zeroline=False, showline=False,
            row=r, col=c
        )

    # Shared color axis (ensure 0 maps to white if using the default scale)
    # If log_scale with non-negative data and log1p, the minimum transformed value is 0.
    fig.update_layout(
        coloraxis=dict(
            colorscale=colorscale,
            cmin=0.0 if log_scale else zmin,   # keep zero at the bottom for log1p; otherwise use data min
            cmax=zmax,
            colorbar=dict(title="Value (log1p)" if log_scale else "Value", len=0.9)
        ),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title=title or f"Calendar heatmap — {year}",
        margin=dict(l=40, r=20, t=60, b=30),
    )

    return fig

