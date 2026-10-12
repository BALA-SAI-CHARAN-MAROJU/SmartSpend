import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

CHART_THEME_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    margin=dict(l=20, r=20, t=35, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

def create_income_expense_trend_chart(daily_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not daily_df.empty:
        fig.add_trace(go.Bar(
            x=daily_df["date"],
            y=daily_df["income"],
            name="Income",
            marker_color="#10b981",
            opacity=0.85
        ))
        fig.add_trace(go.Bar(
            x=daily_df["date"],
            y=daily_df["expense"],
            name="Expense",
            marker_color="#ef4444",
            opacity=0.85
        ))
    fig.update_layout(
        **CHART_THEME_LAYOUT,
        barmode="group",
        title="Income vs Expenses Over Time",
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Amount")
    )
    return fig

def create_category_pie_chart(cat_df: pd.DataFrame) -> go.Figure:
    if cat_df.empty:
        fig = go.Figure()
        fig.update_layout(**CHART_THEME_LAYOUT, title="No Category Data Available")
        return fig

    fig = px.pie(
        cat_df,
        names="category",
        values="total_amount",
        hole=0.55,
        title="Expense Breakdown by Category",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(**CHART_THEME_LAYOUT)
    return fig

def create_monthly_comparison_chart(monthly_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not monthly_df.empty:
        fig.add_trace(go.Bar(
            x=monthly_df["year_month"],
            y=monthly_df["income"],
            name="Income",
            marker_color="#10b981"
        ))
        fig.add_trace(go.Bar(
            x=monthly_df["year_month"],
            y=monthly_df["expense"],
            name="Expense",
            marker_color="#ef4444"
        ))
        fig.add_trace(go.Scatter(
            x=monthly_df["year_month"],
            y=monthly_df["net"],
            name="Net Savings",
            mode="lines+markers",
            line=dict(color="#3b82f6", width=3)
        ))
    fig.update_layout(
        **CHART_THEME_LAYOUT,
        barmode="group",
        title="Monthly Income vs Spending vs Net Savings",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6")
    )
    return fig

def create_forecast_chart(daily_forecasts: List[Dict[str, Any]], recent_history: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    if not recent_history.empty:
        fig.add_trace(go.Scatter(
            x=recent_history["date"],
            y=recent_history["amount"],
            mode="lines+markers",
            name="Actual Daily Spend",
            line=dict(color="#6b7280", width=2),
            marker=dict(size=4)
        ))

    if daily_forecasts:
        f_dates = [f["date"] for f in daily_forecasts]
        f_preds = [f["predicted_spend"] for f in daily_forecasts]
        f_lowers = [f["lower_bound"] for f in daily_forecasts]
        f_uppers = [f["upper_bound"] for f in daily_forecasts]

        fig.add_trace(go.Scatter(
            x=f_dates + f_dates[::-1],
            y=f_uppers + f_lowers[::-1],
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Uncertainty Range (±MAE)"
        ))

        fig.add_trace(go.Scatter(
            x=f_dates,
            y=f_preds,
            mode="lines+markers",
            name="Forecasted Spend",
            line=dict(color="#2563eb", width=2.5, dash="dash"),
            marker=dict(size=6, color="#2563eb")
        ))

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title="Daily Spending Forecast for Remaining Days of the Month",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Amount")
    )
    return fig
