import streamlit as st
from components.styles import format_currency

def render_metric_card(title: str, value: float, currency: str = "INR", subtext: str = "", delta_color: str = "normal"):
    val_str = format_currency(value, currency)
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{val_str}</div>
            {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)

def render_text_metric_card(title: str, text_value: str, subtext: str = ""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value" style="font-size: 1.35rem;">{text_value}</div>
            {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)
