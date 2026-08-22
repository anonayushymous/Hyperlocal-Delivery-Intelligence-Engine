import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from config import DB_URI

def load_experiment_data(engine):
    """
    Extracts user session funnel outcomes and net order economics grouped by A/B variant.
    """
    query = """
    WITH session_summary AS (
        SELECT 
            e.session_id,
            e.user_id,
            u.experiment_group,
            MAX(CASE WHEN e.event_name = 'checkout_start' THEN 1 ELSE 0 END) AS reached_checkout,
            MAX(CASE WHEN e.event_name = 'order_placed' THEN 1 ELSE 0 END) AS converted
        FROM fct_order_events e
        JOIN dim_users u ON e.user_id = u.user_id
        GROUP BY e.session_id, e.user_id, u.experiment_group
    ),
    order_rev AS (
        SELECT 
            user_id,
            (order_value + delivery_fee + surge_fee) AS gross_revenue,
            surge_fee
        FROM fct_orders
        WHERE status = 'delivered'
    )
    SELECT 
        s.session_id,
        s.user_id,
        s.experiment_group,
        s.reached_checkout,
        s.converted,
        COALESCE(o.gross_revenue, 0.0) AS net_revenue,
        COALESCE(o.surge_fee, 0.0) AS surge_fee
    FROM session_summary s
    LEFT JOIN order_rev o ON s.user_id = o.user_id AND s.converted = 1;
    """
    return pd.read_sql(query, engine)

def evaluate_ab_experiment(df):
    """
    Performs parametric and non-parametric hypothesis tests on conversion rate & AOV.
    """
    control = df[df['experiment_group'] == 'control_flat_fee']
    treatment = df[df['experiment_group'] == 'treatment_dynamic_surge']

    # 1. Checkout-to-Order Conversion Rate (Chi-Square Test of Independence)
    ctrl_checkout = control[control['reached_checkout'] == 1]
    treat_checkout = treatment[treatment['reached_checkout'] == 1]

    contingency_table = [
        [ctrl_checkout['converted'].sum(), len(ctrl_checkout) - ctrl_checkout['converted'].sum()],
        [treat_checkout['converted'].sum(), len(treat_checkout) - treat_checkout['converted'].sum()]
    ]
    chi2_stat, p_val_conv, dof, _ = stats.chi2_contingency(contingency_table)

    ctrl_conv_rate = ctrl_checkout['converted'].mean() * 100
    treat_conv_rate = treat_checkout['converted'].mean() * 100

    # 2. Average Order Value / Net Revenue per Converted Order (Two-Sample Welch's t-test)
    ctrl_orders = control[control['converted'] == 1]['net_revenue']
    treat_orders = treatment[treatment['converted'] == 1]['net_revenue']

    t_stat_rev, p_val_rev = stats.ttest_ind(treat_orders, ctrl_orders, equal_var=False)
    
    # 3. Non-Parametric Check (Mann-Whitney U for skewed revenue distributions)
    u_stat, p_val_mwu = stats.mannwhitneyu(treat_orders, ctrl_orders, alternative='two-sided')

    # Summary Metrics Calculation
    ctrl_aov = ctrl_orders.mean()
    treat_aov = treat_orders.mean()
    aov_uplift_pct = ((treat_aov - ctrl_aov) / ctrl_aov) * 100
    conv_drop_pct = treat_conv_rate - ctrl_conv_rate

    results = {
        "Metric": [
            "Sample Size (Sessions)",
            "Checkout-to-Order Conversion Rate",
            "Chi-Square p-value (Conversion)",
            "Average Order Value (AOV)",
            "AOV Uplift (%)",
            "Welch's t-test p-value (AOV)",
            "Mann-Whitney U p-value (AOV)",
            "Statistically Significant Result (alpha=0.05)"
        ],
        "Control (Flat Fee)": [
            f"{len(control):,}",
            f"{ctrl_conv_rate:.2f}%",
            "-",
            f"₹{ctrl_aov:.2f}",
            "-",
            "-",
            "-",
            "-"
        ],
        "Treatment (Dynamic Surge)": [
            f"{len(treatment):,}",
            f"{treat_conv_rate:.2f}% ({conv_drop_pct:+.2f}%)",
            f"{p_val_conv:.4e}",
            f"₹{treat_aov:.2f} ({aov_uplift_pct:+.2f}%)",
            f"{aov_uplift_pct:+.2f}%",
            f"{p_val_rev:.4e}",
            f"{p_val_mwu:.4e}",
            "YES" if (p_val_conv < 0.05 and p_val_rev < 0.05) else "NO"
        ]
    }
    
    return pd.DataFrame(results), {
        "ctrl_conv": ctrl_conv_rate,
        "treat_conv": treat_conv_rate,
        "p_val_conv": p_val_conv,
        "ctrl_aov": ctrl_aov,
        "treat_aov": treat_aov,
        "p_val_rev": p_val_rev
    }

if __name__ == "__main__":
    print("[*] Connecting to database for A/B experiment evaluation...")
    engine = create_engine(DB_URI)
    try:
        df_exp = load_experiment_data(engine)
        if df_exp.empty:
            print("[!] No records found. Ensure db_loader.py has populated tables.")
        else:
            df_report, raw_metrics = evaluate_ab_experiment(df_exp)
            print("\n========================================================")
            print("         A/B EXPERIMENT: DYNAMIC SURGE PRICING         ")
            print("========================================================")
            print(df_report.to_string(index=False))
            print("========================================================\n")
    except Exception as e:
        print(f"[!] Evaluation failed: {e}")