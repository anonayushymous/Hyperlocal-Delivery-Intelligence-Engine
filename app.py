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

st.set_page_config(
    page_title="Hyperlocal Delivery & Marketplace Intelligence Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, simple UI styling
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
    .card-help {
        font-size: 0.78rem;
        color: #10b981;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    return create_engine(DB_URI)

# -----------------------------------------------------------------------------
# SQL Queries
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_sales_summary():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(order_value + delivery_fee + surge_fee) AS total_sales,
            AVG(order_value) AS avg_bill,
            SUM(surge_fee) AS surge_money,
            AVG(delivery_time_mins) AS avg_time,
            ROUND(SUM(CASE WHEN status = 'delivered' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(order_id), 1) AS success_rate
        FROM fct_orders;
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
            SUM(s1) AS "1. Searched Item",
            SUM(s2) AS "2. Added to Cart",
            SUM(s3) AS "3. Clicked Checkout",
            SUM(s4) AS "4. Paid & Placed Order"
        FROM stages;
    """, engine)

@st.cache_data(ttl=300)
def load_store_delays_and_geo():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            o.dark_store_id AS "Store ID",
            s.zone AS "Location Name",
            s.lat,
            s.lon,
            COUNT(o.order_id) AS "Total Orders",
            ROUND(AVG(o.delivery_time_mins), 1) AS "Average Delivery Time (Mins)",
            SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1 ELSE 0 END) AS "Late Deliveries",
            ROUND(SUM(CASE WHEN o.delivery_time_mins > o.sla_target_mins THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(o.order_id), 1) AS "Late Rate (%)"
        FROM fct_orders o
        JOIN dim_dark_stores s ON o.dark_store_id = s.dark_store_id
        WHERE o.status = 'delivered'
        GROUP BY o.dark_store_id, s.zone, s.lat, s.lon
        ORDER BY "Late Rate (%)" DESC;
    """, engine)

@st.cache_data(ttl=300)
def load_rider_performance():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            r.rider_id AS "Rider ID",
            r.vehicle_type AS "Vehicle",
            r.rating AS "Rating",
            COUNT(o.order_id) AS "Deliveries Completed",
            ROUND(AVG(o.delivery_time_mins), 1) AS "Avg Delivery Speed (Mins)",
            ROUND(SUM(CASE WHEN o.delivery_time_mins <= o.sla_target_mins THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(o.order_id), 1) AS "On-Time Rate (%)"
        FROM fct_orders o
        JOIN dim_riders r ON o.rider_id = r.rider_id
        WHERE o.status = 'delivered'
        GROUP BY r.rider_id, r.vehicle_type, r.rating
        ORDER BY "Deliveries Completed" DESC
        LIMIT 15;
    """, engine)

@st.cache_data(ttl=300)
def load_delivery_time_distribution():
    engine = get_engine()
    return pd.read_sql("SELECT delivery_time_mins FROM fct_orders WHERE status = 'delivered';", engine)

@st.cache_data(ttl=300)
def load_failed_reasons():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            failure_reason AS "Reason",
            COUNT(order_id) AS "Total Orders"
        FROM fct_orders
        WHERE status != 'delivered' AND failure_reason IS NOT NULL
        GROUP BY failure_reason
        ORDER BY "Total Orders" DESC;
    """, engine)

@st.cache_data(ttl=300)
def load_complaints_by_zone():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            s.zone AS "City Area",
            o.complaint_reason AS "Complaint Type",
            COUNT(o.order_id) AS "Total Complaints"
        FROM fct_orders o
        JOIN dim_dark_stores s ON o.dark_store_id = s.dark_store_id
        WHERE o.complaint_reason IS NOT NULL
        GROUP BY s.zone, o.complaint_reason
        ORDER BY "Total Complaints" DESC;
    """, engine)

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ Hyperlocal Intelligence")
st.sidebar.caption("10-Minute Delivery Analytics Hub")

page = st.sidebar.radio(
    "Choose a Module:",
    [
        "1. Sales & Growth Overview",
        "2. Warehouse & Rider Operations",
        "3. Delivery Quality & Root Cause Analysis",
        "4. Dynamic Surge Pricing A/B Test"
    ]
)

st.sidebar.write("---")
st.sidebar.info("💡 **Promise:** Delivering customer orders in under 12 minutes.")

# -----------------------------------------------------------------------------
# PAGE 1: Sales & Growth Overview
# -----------------------------------------------------------------------------
if page == "1. Sales & Growth Overview":
    st.title("💰 Sales & Customer Demand")
    st.write("Tracks total money made, order success rates, and customer drop-off across the shopping funnel.")
    st.write("")

    try:
        sales_data = load_sales_summary()
        orders = sales_data['total_orders'].iloc[0]
        total_money = sales_data['total_sales'].iloc[0]
        avg_bill = sales_data['avg_bill'].iloc[0]
        success_rate = sales_data['success_rate'].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TOTAL SALES COLLECTED</div>
                <div class="card-value">₹{total_money:,.0f}</div>
                <div class="card-help">Total platform revenue</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TOTAL ORDERS PLACED</div>
                <div class="card-value">{orders:,}</div>
                <div class="card-help">From all active stores</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">DELIVERY SUCCESS RATE</div>
                <div class="card-value">{success_rate:.1f}%</div>
                <div class="card-help">Successfully reached doorstep</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">AVERAGE BILL PER ORDER</div>
                <div class="card-value">₹{avg_bill:.0f}</div>
                <div class="card-help">Average basket size</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")
        
        st.subheader("Customer Shopping Funnel (Drop-Off Points)")
        st.caption("Tracks users step-by-step from searching an item to paying.")

        funnel_df = load_customer_steps()
        if not funnel_df.empty:
            fig = go.Figure(go.Funnel(
                y=funnel_df.columns.tolist(),
                x=funnel_df.iloc[0].values,
                textinfo="value+percent previous",
                marker={"color": ["#334155", "#475569", "#64748b", "#2563eb"]}
            ))
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width='stretch')

        st.info("""
        **What does this funnel show?**
        * **Search ➔ Cart Drop:** Around 15% of people do not add items to cart (usually due to items being out of stock).
        * **Checkout Completion:** 90% of shoppers who open the checkout screen complete payment successfully.
        """)

    except Exception as e:
        st.error(f"Please run python db_loader.py first. Error: {e}")

# -----------------------------------------------------------------------------
# PAGE 2: Warehouse & Rider Operations
# -----------------------------------------------------------------------------
elif page == "2. Warehouse & Rider Operations":
    st.title("⏱️ Dark Store & Rider Fleet Operations")
    st.write("Tracks delivery delays across local stores and top rider performance.")
    st.write("")

    try:
        stores = load_store_delays_and_geo()
        total_late = stores["Late Deliveries"].sum()
        avg_speed = stores["Average Delivery Time (Mins)"].mean()

        d1, d2 = st.columns(2)
        with d1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TOTAL LATE ORDERS (>12 MINS)</div>
                <div class="card-value">{total_late:,} orders</div>
                <div class="card-help" style="color:#ef4444;">Exceeded the 12-min promise</div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">AVERAGE DELIVERY TIME</div>
                <div class="card-value">{avg_speed:.1f} minutes</div>
                <div class="card-help">Across the entire city fleet</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")

        st.subheader("Which local stores have the most delays?")
        st.caption("Stores above the 10% line need more delivery riders or better warehouse layout.")

        fig_bar = px.bar(
            stores,
            x="Location Name",
            y="Late Rate (%)",
            color="Late Rate (%)",
            color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
            text="Late Rate (%)"
        )
        fig_bar.add_hline(y=10.0, line_dash="dash", line_color="#ef4444", annotation_text="Warning Threshold (10%)")
        fig_bar.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width='stretch')

        st.write("---")
        st.subheader("🛵 Top Rider Performance Leaderboard")
        st.caption("Riders with the highest on-time delivery rates and customer ratings.")
        riders_df = load_rider_performance()
        st.dataframe(riders_df, width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# PAGE 3: Delivery Quality & Root Cause Analysis
# -----------------------------------------------------------------------------
elif page == "3. Delivery Quality & Root Cause Analysis":
    st.title("🔍 Quality, Complaints & Why Orders Fail")
    st.write("Diagnosing delivery time spread, failed deliveries, and customer complaints.")
    st.write("")

    try:
        q1, q2 = st.columns(2)

        # 1. Delivery Time Bell Curve
        with q1:
            st.subheader("Delivery Time Spread (Bell Curve)")
            st.caption("Most orders arrive within 9 to 13 minutes.")
            del_df = load_delivery_time_distribution()
            fig_hist = px.histogram(
                del_df,
                x="delivery_time_mins",
                nbins=35,
                color_discrete_sequence=["#2563eb"],
                labels={"delivery_time_mins": "Delivery Time (Minutes)"}
            )
            fig_hist.add_vline(x=12.0, line_dash="dash", line_color="#ef4444", annotation_text="12 Min SLA Target")
            fig_hist.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), yaxis_title="Number of Orders")
            st.plotly_chart(fig_hist, width='stretch')

        # 2. Failed Delivery Root Cause Breakdown
        with q2:
            st.subheader("Why Do Deliveries Fail?")
            st.caption("Breakdown of reasons for undelivered orders.")
            fail_df = load_failed_reasons()
            fig_pie = px.pie(
                fail_df,
                names="Reason",
                values="Total Orders",
                color_discrete_sequence=px.colors.sequential.Reds_r,
                hole=0.4
            )
            fig_pie.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_pie, width='stretch')

        st.write("---")
        st.subheader("Customer Complaints by Area")
        st.caption("Tracking issues like late delivery, damaged items, or missing products.")
        
        comp_df = load_complaints_by_zone()
        fig_comp = px.bar(
            comp_df,
            x="City Area",
            y="Total Complaints",
            color="Complaint Type",
            barmode="stack",
            height=360
        )
        fig_comp.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig_comp, width='stretch')

    except Exception as e:
        st.error(f"Error loading quality diagnostics: {e}")

# -----------------------------------------------------------------------------
# PAGE 4: Dynamic Surge Pricing A/B Test
# -----------------------------------------------------------------------------
elif page == "4. Dynamic Surge Pricing A/B Test":
    st.title("🧪 Extra Rush Fee Experiment (A/B Test)")
    st.write("We tested charging an extra **₹20 to ₹50 rush fee** during peak hours (7 PM – 10 PM) on half our users.")
    st.write("")

    try:
        engine = get_engine()
        df_exp = load_experiment_data(engine)
        report_df, raw = evaluate_ab_experiment(df_exp)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">NORMAL USERS (FLAT ₹15 FEE)</div>
                <div class="card-value">₹{raw['ctrl_aov']:.0f} bill</div>
                <div class="card-help">{raw['ctrl_conv']:.1f}% ended up ordering</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">TEST USERS (RUSH-HOUR SURGE FEE)</div>
                <div class="card-value">₹{raw['treat_aov']:.0f} bill</div>
                <div class="card-help">{raw['treat_conv']:.1f}% ended up ordering</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            extra_per_order = raw['treat_aov'] - raw['ctrl_aov']
            st.markdown(f"""
            <div class="card">
                <div class="card-title">EXTRA PROFIT PER ORDER</div>
                <div class="card-value">+₹{extra_per_order:.0f}</div>
                <div class="card-help" style="color:#2563eb;">Net gain per delivery</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("---")

        g1, g2 = st.columns(2)

        with g1:
            st.subheader("1. Average Money Spent Per Order")
            st.caption("Did users in the test group spend more money?")
            df_aov = pd.DataFrame({
                "Variant": ["Normal Users (Flat ₹15)", "Test Users (Rush Fee)"],
                "Average Bill (₹)": [round(raw['ctrl_aov'], 1), round(raw['treat_aov'], 1)]
            })
            fig_aov = px.bar(df_aov, x="Variant", y="Average Bill (₹)", text="Average Bill (₹)", color="Variant", color_discrete_sequence=["#64748b", "#2563eb"])
            fig_aov.update_traces(texttemplate='₹%{text}', textposition='outside')
            fig_aov.update_layout(height=330, showlegend=False, margin=dict(l=20, r=20, t=30, b=20), yaxis_range=[0, max(raw['ctrl_aov'], raw['treat_aov']) * 1.25])
            st.plotly_chart(fig_aov, width='stretch')

        with g2:
            st.subheader("2. Percentage of Users Who Ordered")
            st.caption("Did the extra fee scare customers away?")
            df_conv = pd.DataFrame({
                "Variant": ["Normal Users (Flat ₹15)", "Test Users (Rush Fee)"],
                "Order Completion Rate (%)": [round(raw['ctrl_conv'], 1), round(raw['treat_conv'], 1)]
            })
            fig_conv = px.bar(df_conv, x="Variant", y="Order Completion Rate (%)", text="Order Completion Rate (%)", color="Variant", color_discrete_sequence=["#64748b", "#f59e0b"])
            fig_conv.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_conv.update_layout(height=330, showlegend=False, margin=dict(l=20, r=20, t=30, b=20), yaxis_range=[0, 100])
            st.plotly_chart(fig_conv, width='stretch')

        st.write("---")
        st.subheader("💡 Final Business Decision")
        st.success("""
        **Recommendation: ROLL OUT RUSH-HOUR SURGE PRICING**
        
        * **The Upside:** We made **₹25 to ₹35 more profit** on every single order.
        * **The Downside:** Only **~1.5% fewer customers** dropped off because of the extra fee.
        * **Conclusion:** The massive revenue gain far outweighs the minor drop in orders.
        """)

    except Exception as e:
        st.error(f"Error reading experiment data: {e}")