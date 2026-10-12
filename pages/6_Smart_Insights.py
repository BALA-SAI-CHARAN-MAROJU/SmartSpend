import streamlit as st
from database.initialization import initialize_database
from database.repositories import SettingsRepository
from services.insight_service import InsightService
from components.styles import apply_custom_styles
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartSpend AI - Insights", page_icon="💳", layout="wide")
initialize_database()
apply_custom_styles()
render_sidebar()

st.title("Smart Financial Insights")
st.caption("Actionable, rule-based heuristics and statistical spending anomalies derived from your real transaction data.")

insight_service = InsightService()
insights = insight_service.generate_insights()

if not insights:
    st.info("No notable spending alerts or anomalies detected. Your finances look stable!")
else:
    for item in insights:
        itype = item.get("type", "info")
        icon = "💡"
        if itype == "danger":
            icon = "🚨"
        elif itype == "warning":
            icon = "⚠️"

        st.markdown(f"""
            <div class="insight-card {itype}">
                <div class="insight-title">{icon} {item['title']}</div>
                <div class="insight-body">{item['message']}</div>
            </div>
        """, unsafe_allow_html=True)
