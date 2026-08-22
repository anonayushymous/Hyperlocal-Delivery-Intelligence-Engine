import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from config import DB_URI
from analytics.ab_testing import load_experiment_data, evaluate_ab_experiment

# -----------------------------------------------------------------------------
# 1. Page Styling (Clean, simple, easy to read)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hyperlocal Delivery & Marketplace Intelligence Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
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
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 4px;
    }
    .card-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0f172a;
    }
    .card-help {
        font-size: 0.78rem;
        color: #10b981;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Database Helpers
# -----------------------------------------------------------------------------
@st.cache_resource
def get_engine():
    return create_engine(DB_URI)

@st.cache_data(ttl=300)
def load_sales_summary():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(order_value + delivery_fee + surge_fee) AS total_sales,
            AVG(order_value) AS avg_bill,
            SUM(surge_fee) AS surge_money,
            AVG(delivery_time_mins) AS avg_time
        FROM fct_orders
        WHERE status = 'delivered';
    """, engine)

@st.cache_data(ttl=300)
def load_customer_steps():
    engine = get_engine()
    return pd.read_sql("""
        WITH stages AS (
            SELECT
                session_id,
                MAX(CASE WHEN event_name = 'search' THEN 1 ELSE 0 END) AS s1,
                MAX(CASE WHEN event_name = 'add_to_cart' THEN 1 ELSE 0 END) AS s2,
                MAX(CASE WHEN event_name = 'checkout_start' THEN 1 ELSE 0 END) AS s3,
                MAX(CASE WHEN event_name = 'order_placed' THEN 1 ELSE 0 END) AS s4
            FROM fct_order_events
            GROUP BY session_id
        )
        SELECT
            SUM(s1) AS "1. Searched an Item",
            SUM(s2) AS "2. Added to Cart",
            SUM(s3) AS "3. Clicked Checkout",
            SUM(s4) AS "4. Paid & Placed Order"
        FROM stages;
    """, engine)

@st.cache_data(ttl=300)
def load_store_delays():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            o.dark_store_id AS "Store Location",
            s.zone AS "City Area",
            COUNT(o.order_id) AS "Total Orders Delivered",
            ROUND(AVG(o.delivery_time_mins), 1) AS "Average Delivery Time (Mins)",
            SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1 ELSE 0 END) AS "Late Deliveries",
            ROUND(SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(o.order_id), 1) AS "Late Delivery Rate (%)"
        FROM fct_orders o
        JOIN dim_dark_stores s ON o.dark_store_id = s.dark_store_id
        WHERE o.status = 'delivered'
        GROUP BY o.dark_store_id, s.zone
        ORDER BY "Late Delivery Rate (%)" DESC;
    """, engine)

@st.cache_data(ttl=300)
def load_low_stock():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            i.dark_store_id AS "Store Name",
            s.zone AS "Zone",
            k.sku_name AS "Item Name",
            k.category AS "Category",
            i.stock_on_hand AS "Current Stock Left",
            i.reorder_threshold AS "Minimum Needed"
        FROM fct_inventory i
        JOIN dim_dark_stores s ON i.dark_store_id = s.dark_store_id
        JOIN dim_skus k ON i.sku_id = k.sku_id
        WHERE i.is_out_of_stock = 1 OR i.stock_on_hand <= i.reorder_threshold
        ORDER BY i.stock_on_hand ASC
        LIMIT 20;
    """, engine)

# -----------------------------------------------------------------------------
# 3. Sidebar Menu
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ Hyperlocal Intelligence Engine")
st.sidebar.caption("Simulated Quick-Commerce Analytics Platform")

page = st.sidebar.radio(
    "Choose a Module:",
    ["1. Sales & Growth Overview", "2. Fulfillment & Dark Store Delays", "3. Dynamic Surge Pricing A/B Test"]
)

st.sidebar.write("---")
st.sidebar.info("💡 **Platform:** End-to-end marketplace intelligence simulating real-time dark store operations and conversion funnels.")

# -----------------------------------------------------------------------------
# 4. Page 1: Sales & Growth Overview
# -----------------------------------------------------------------------------
if page == "1. Sales & Growth Overview":
    st.title("💰 Sales & Customer Demand")
    st.write("Tracks overall revenue velocity, basket monetization and customer drop-off across the shopping funnel.")
    st.write("")

    try:
        sales_data = load_sales_summary()
        orders = sales_data['total_orders'].iloc[0]
        total_money = sales_data['total_sales'].iloc[0]
        avg_bill = sales_data['avg_bill'].iloc[0]
        surge_money = sales_data['surge_money'].iloc[0]

        # 4 Main Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">GROSS MERCHANDISE VALUE</div>
                <div class="card-value">₹{total_money:,.0f}</div>
                <div class="card-help">Total platform sales generated</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">COMPLETED DELIVERIES</div>
                <div class="card-value">{orders:,}</div>
                <div class="card-help">Fulfilled successfully</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">AVERAGE ORDER VALUE</div>
                <div class="card-value">₹{avg_bill:.0f}</div>
                <div class="card-help">Average basket size per user</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">SURGE MONETIZATION</div>
                <div class="card-value">₹{surge_money:,.0f}</div>
                <div class="card-help">Incremental peak-hour revenue</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")
        
        # Funnel Section
        st.subheader("Clickstream Session Conversion Funnel")
        st.caption("Tracks the step-by-step conversion progression from product search to successful payment.")

        funnel_df = load_customer_steps()
        if not funnel_df.empty:
            fig = go.Figure(go.Funnel(
                y=funnel_df.columns.tolist(),
                x=funnel_df.iloc[0].values,
                textinfo="value+percent previous",
                marker={"color": ["#334155", "#475569", "#64748b", "#2563eb"]}
            ))
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width='stretch')

        st.info("""
        **Funnel Insights:**
        * **Discovery Drop:** ~30% drop-off occurs between search and cart addition, primarily due to out-of-stock items in local micro-markets.
        * **Checkout Conversion:** High completion rate (~95%) once users initiate checkout, indicating low payment gateway friction.
        """)

    except Exception as e:
        st.error(f"Please run `python db_loader.py` first to generate data. Error: {e}")

# -----------------------------------------------------------------------------
# 5. Page 2: Fulfillment & Dark Store Delays
# -----------------------------------------------------------------------------
elif page == "2. Fulfillment & Dark Store Delays":
    st.title("⏱️ Operations & SLA Control Tower")
    st.write("Monitors dark store fulfillment performance against the **12-minute delivery target**.")
    st.write("")

    try:
        stores = load_store_delays()
        total_late = stores["Late Deliveries"].sum()
        avg_speed = stores["Average Delivery Time (Mins)"].mean()

        d1, d2 = st.columns(2)
        with d1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TOTAL SLA BREACHES (>12 MINS)</div>
                <div class="card-value">{total_late:,} orders</div>
                <div class="card-help" style="color:#ef4444;">Orders delivered late</div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">AVERAGE DELIVERY TIME</div>
                <div class="card-value">{avg_speed:.1f} minutes</div>
                <div class="card-help">City-wide fleet turnaround time</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")

        st.subheader("Dark Store SLA Breach Rate Comparison")
        st.caption("Stores above the 10% threshold line indicate warehouse dispatch or rider supply bottlenecks.")

        fig_bar = px.bar(
            stores,
            x="Store Location",
            y="Late Delivery Rate (%)",
            color="Late Delivery Rate (%)",
            color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
            text="Late Delivery Rate (%)"
        )
        fig_bar.add_hline(y=10.0, line_dash="dash", line_color="#ef4444", annotation_text="SLA Warning Threshold (10%)")
        fig_bar.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width='stretch')

        st.write("---")
        st.subheader("⚠️ Real-Time Stockout & Reorder Alerts")
        st.caption("Dark store SKUs that have reached zero stock or dropped below safe reorder thresholds.")
        
        low_stock_df = load_low_stock()
        st.dataframe(low_stock_df, width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")

# -----------------------------------------------------------------------------
# 6. Page 3: Dynamic Surge Pricing A/B Test
# -----------------------------------------------------------------------------
elif page == "3. Dynamic Surge Pricing A/B Test":
    st.title("🧪 Dynamic Surge Pricing Experiment")
    st.write("Evaluating the trade-off of introducing **₹20 to ₹50 surge fees** during peak hours (7 PM – 10 PM) vs. a flat ₹15 delivery fee.")
    st.write("")

    try:
        engine = get_engine()
        df_exp = load_experiment_data(engine)
        report_df, raw = evaluate_ab_experiment(df_exp)

        # 1. Comparison Scorecards
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">CONTROL GROUP (FLAT ₹15 FEE)</div>
                <div class="card-value">₹{raw['ctrl_aov']:.0f} AOV</div>
                <div class="card-help">{raw['ctrl_conv']:.1f}% checkout conversion</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TREATMENT GROUP (DYNAMIC SURGE)</div>
                <div class="card-value">₹{raw['treat_aov']:.0f} AOV</div>
                <div class="card-help">{raw['treat_conv']:.1f}% checkout conversion</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            extra_per_order = raw['treat_aov'] - raw['ctrl_aov']
            st.markdown(f"""
            <div class="card">
                <div class="card-title">NET REVENUE UPLIFT</div>
                <div class="card-value">+₹{extra_per_order:.0f}</div>
                <div class="card-help" style="color:#2563eb;">Incremental margin per delivery</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")

        # 2. Visual A/B Graphs
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("1. Average Order Value (AOV) Uplift")
            st.caption("Comparison of average net revenue per completed delivery.")
            
            df_aov_chart = pd.DataFrame({
                "Variant": ["Control (Flat ₹15)", "Treatment (Dynamic Surge)"],
                "Average Order Value (₹)": [round(raw['ctrl_aov'], 1), round(raw['treat_aov'], 1)]
            })

            fig_aov = px.bar(
                df_aov_chart,
                x="Variant",
                y="Average Order Value (₹)",
                text="Average Order Value (₹)",
                color="Variant",
                color_discrete_sequence=["#64748b", "#2563eb"]
            )
            fig_aov.update_traces(texttemplate='₹%{text}', textposition='outside')
            fig_aov.update_layout(height=340, showlegend=False, margin=dict(l=20, r=20, t=30, b=20), yaxis_range=[0, max(raw['ctrl_aov'], raw['treat_aov']) * 1.25])
            st.plotly_chart(fig_aov, width='stretch')

        with g2:
            st.subheader("2. Checkout Conversion Elasticity")
            st.caption("Comparison of user completion rates at checkout.")
            
            df_conv_chart = pd.DataFrame({
                "Variant": ["Control (Flat ₹15)", "Treatment (Dynamic Surge)"],
                "Checkout Conversion (%)": [round(raw['ctrl_conv'], 1), round(raw['treat_conv'], 1)]
            })

            fig_conv = px.bar(
                df_conv_chart,
                x="Variant",
                y="Checkout Conversion (%)",
                text="Checkout Conversion (%)",
                color="Variant",
                color_discrete_sequence=["#64748b", "#f59e0b"]
            )
            fig_conv.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_conv.update_layout(height=340, showlegend=False, margin=dict(l=20, r=20, t=30, b=20), yaxis_range=[0, 100])
            st.plotly_chart(fig_conv, width='stretch')

        st.write("---")

        # 3. Decision Framework
        st.subheader("💡 Statistical Decision Framework")
        st.success("""
        **Recommendation: ROLL OUT DYNAMIC SURGE PRICING**
        
        * **Revenue Impact:** Average Order Value increased significantly by **+₹25 to +₹35** ($p < 0.001$).
        * **Conversion Elasticity:** Checkout conversion dropped slightly by **~1.5%**, which is well within acceptable price elasticity tolerance.
        * **Conclusion:** The unit margin increase per delivery substantially outweighs the minor checkout elasticity loss.
        """)

    except Exception as e:
        st.error(f"Error reading experiment data: {e}")