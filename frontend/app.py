import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

API_URL = os.getenv("API_URL", "http://backend:8000")

st.set_page_config(
    page_title="Hyperlocal Delivery & Marketplace Intelligence Engine",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .card-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 4px;
    }
    .card-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("⚡ Hyperlocal Intelligence")
st.sidebar.caption("10-Minute Delivery Analytics Hub")

page = st.sidebar.radio("Choose a Module:", ["1. Sales & Growth Overview", "2. Warehouse & Rider Operations"])

if page == "1. Sales & Growth Overview":
    st.title("💰 Sales & Customer Demand")
    st.write("Real-time telemetry served via FastAPI microservice.")

    try:
        res = requests.get(f"{API_URL}/api/v1/metrics/sales-summary", timeout=10)
        sales = res.json()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="card"><div class="card-title">TOTAL SALES</div><div class="card-value">₹{sales["total_sales"]:,.0f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><div class="card-title">TOTAL ORDERS</div><div class="card-value">{sales["total_orders"]:,}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><div class="card-title">SUCCESS RATE</div><div class="card-value">{sales["success_rate"]:.1f}%</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="card"><div class="card-title">AVG BILL</div><div class="card-value">₹{sales["avg_bill"]:.0f}</div></div>', unsafe_allow_html=True)

        st.write("---")
        st.subheader("Customer Shopping Funnel")

        f_res = requests.get(f"{API_URL}/api/v1/metrics/funnel", timeout=10)
        funnel_data = f_res.json()
        if funnel_data:
            df_funnel = pd.DataFrame(funnel_data)
            fig = go.Figure(go.Funnel(
                y=df_funnel["stage"],
                x=df_funnel["count"],
                textinfo="value+percent previous",
                marker={"color": ["#334155", "#475569", "#64748b", "#2563eb"]}
            ))
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to fetch data from backend API: {e}")

elif page == "2. Warehouse & Rider Operations":
    st.title("⏱️ Dark Store & Rider Fleet Operations")
    try:
        s_res = requests.get(f"{API_URL}/api/v1/metrics/store-delays", timeout=10)
        stores = pd.DataFrame(s_res.json())

        if not stores.empty:
            fig_bar = px.bar(
                stores,
                x="location_name",
                y="late_rate_pct",
                color="late_rate_pct",
                color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
                text="late_rate_pct",
                labels={"location_name": "Store Location", "late_rate_pct": "Late Rate (%)"}
            )
            fig_bar.add_hline(y=10.0, line_dash="dash", line_color="#ef4444", annotation_text="Warning (10%)")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.write("---")
        st.subheader("🛵 Top Rider Leaderboard")
        r_res = requests.get(f"{API_URL}/api/v1/metrics/rider-performance", timeout=10)
        riders_df = pd.DataFrame(r_res.json())
        if not riders_df.empty:
            st.dataframe(riders_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to fetch operations telemetry: {e}")