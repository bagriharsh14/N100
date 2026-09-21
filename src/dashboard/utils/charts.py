import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_radar_chart(categories, values, title, name="Company", group_avg=None):
    """Create interactive Plotly radar chart."""
    fig = go.Figure()

    # Company trace
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=name,
        line=dict(color="#1e3a8a", width=2),
        fillcolor="rgba(30, 58, 138, 0.25)"
    ))

    # Benchmark/Group Average trace if provided
    if group_avg is not None:
        fig.add_trace(go.Scatterpolar(
            r=group_avg + [group_avg[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name="Peer Median",
            line=dict(color="#ea580c", width=1.5, dash="dash"),
            fillcolor="rgba(234, 88, 12, 0.1)"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=8),
                color="#64748b"
            )
        ),
        title=dict(text=title, font=dict(size=14, color="#1e293b")),
        showlegend=True,
        margin=dict(l=40, r=40, t=40, b=40),
        height=380
    )
    return fig


def create_trend_line_chart(df: pd.DataFrame, x_col: str, y_cols: list, title: str):
    """Create multi-metric line trend chart."""
    fig = go.Figure()
    colors = ["#1e3a8a", "#059669", "#d97706", "#dc2626", "#7c3aed"]

    for idx, col in enumerate(y_cols):
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[col],
                mode="lines+markers",
                name=col.replace("_", " ").title(),
                line=dict(color=colors[idx % len(colors)], width=2.5),
                marker=dict(size=6)
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#1e293b")),
        xaxis=dict(title=x_col.replace("_", " ").title(), tickangle=35),
        yaxis=dict(title="Value"),
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
        height=380
    )
    return fig
