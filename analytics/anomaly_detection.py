import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from config import DB_URI

def load_fulfillment_timeseries(engine):
    """
    Extracts hourly fulfillment performance per dark store.
    """
    query = """
    SELECT 
        dark_store_id,
        DATE_TRUNC('hour', placed_at) AS order_hour,
        COUNT(order_id) AS total_orders,
        AVG(delivery_time_mins) AS avg_delivery_time_mins,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY delivery_time_mins) AS p95_delivery_time_mins,
        SUM(CASE WHEN delivery_time_mins > sla_target_mins THEN 1 ELSE 0 END) AS sla_breaches
    FROM fct_orders
    WHERE status = 'delivered'
    GROUP BY dark_store_id, DATE_TRUNC('hour', placed_at)
    ORDER BY dark_store_id, order_hour;
    """
    return pd.read_sql(query, engine)

def detect_fulfillment_anomalies(df):
    """
    Flags store-hours where delivery SLA breaches or P95 fulfillment exceed statistical baselines.
    """
    if df.empty:
        return pd.DataFrame()

    df['breach_rate'] = (df['sla_breaches'] / df['total_orders']) * 100.0
    
    # 1. IQR-Based Outlier Detection on P95 Delivery Time
    q1 = df['p95_delivery_time_mins'].quantile(0.25)
    q3 = df['p95_delivery_time_mins'].quantile(0.75)
    iqr = q3 - q1
    upper_threshold_iqr = q3 + (1.5 * iqr)
    
    df['is_p95_iqr_anomaly'] = df['p95_delivery_time_mins'] > upper_threshold_iqr

    # 2. Z-Score Anomaly Detection on SLA Breach Rate
    mean_breach = df['breach_rate'].mean()
    std_breach = df['breach_rate'].std()
    
    if std_breach > 0:
        df['z_score_breach'] = (df['breach_rate'] - mean_breach) / std_breach
        df['is_breach_zscore_anomaly'] = df['z_score_breach'] > 2.5
    else:
        df['z_score_breach'] = 0.0
        df['is_breach_zscore_anomaly'] = False

    # Combined Anomaly Flag
    df['anomaly_detected'] = df['is_p95_iqr_anomaly'] | df['is_breach_zscore_anomaly']
    
    anomalies = df[df['anomaly_detected']].copy()
    anomalies['severity'] = np.where(
        anomalies['is_p95_iqr_anomaly'] & anomalies['is_breach_zscore_anomaly'],
        'CRITICAL',
        'HIGH'
    )
    
    return anomalies.sort_values(by='order_hour', ascending=False)

if __name__ == "__main__":
    print("[*] Connecting to database for dark store anomaly detection...")
    engine = create_engine(DB_URI)
    try:
        df_timeseries = load_fulfillment_timeseries(engine)
        if df_timeseries.empty:
            print("[!] No records found. Ensure db_loader.py has populated tables.")
        else:
            anomalies = detect_fulfillment_anomalies(df_timeseries)
            print("\n========================================================")
            print(f"      OPERATIONAL ANOMALIES DETECTED ({len(anomalies)} incidents)      ")
            print("========================================================")
            if not anomalies.empty:
                cols_to_print = [
                    'dark_store_id', 'order_hour', 'total_orders', 
                    'p95_delivery_time_mins', 'breach_rate', 'severity'
                ]
                print(anomalies[cols_to_print].head(10).to_string(index=False))
            else:
                print("No fulfillment anomalies identified. Operations within normal bounds.")
            print("========================================================\n")
    except Exception as e:
        print(f"[!] Anomaly detection failed: {e}")