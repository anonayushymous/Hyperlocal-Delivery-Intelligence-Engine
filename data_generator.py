import numpy as np
import pandas as pd
from faker import Faker
import datetime
import random

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

def generate_all_data(n_users=10000, n_orders=50000):
    print("Generating users and dark stores...")
    # 1. Dark Stores Dimension
    dark_stores = [
        {"dark_store_id": f"DS_{i:02d}", "zone": f"Zone_{chr(65 + i%6)}", "capacity_orders_per_hr": np.random.randint(60, 150)}
        for i in range(1, 13)
    ]
    df_stores = pd.DataFrame(dark_stores)

    # 2. Users Dimension
    user_ids = [f"U_{i:06d}" for i in range(n_users)]
    user_records = []
    for uid in user_ids:
        signup_dt = fake.date_time_between(start_date='-180d', end_date='now')
        user_records.append({
            "user_id": uid,
            "signup_at": signup_dt,
            "city_tier": np.random.choice(["Tier-1", "Tier-2"], p=[0.75, 0.25]),
            "acquisition_channel": np.random.choice(["Meta_Ads", "Google_Search", "Organic", "Referral"], p=[0.35, 0.30, 0.25, 0.10]),
            "experiment_group": np.random.choice(["control_flat_fee", "treatment_dynamic_surge"], p=[0.50, 0.50])
        })
    df_users = pd.DataFrame(user_records)

    # 3. SKU / Product Catalog Dimension
    categories = ["Dairy & Eggs", "Beverages", "Snacks & Munchies", "Instant Food", "Fresh Produce"]
    skus = []
    for i in range(1, 101):
        cat = np.random.choice(categories)
        base_price = round(np.random.uniform(20.0, 500.0), 2)
        skus.append({
            "sku_id": f"SKU_{i:04d}",
            "sku_name": f"{cat} Item {i}",
            "category": cat,
            "cost_price": round(base_price * 0.75, 2),
            "selling_price": base_price
        })
    df_skus = pd.DataFrame(skus)

    # 4. Inventory Snapshots
    print("Generating inventory snapshots...")
    inventory_records = []
    for store in df_stores["dark_store_id"]:
        for sku in df_skus["sku_id"]:
            stock_level = np.random.randint(0, 45)
            threshold = 10
            inventory_records.append({
                "dark_store_id": store,
                "sku_id": sku,
                "stock_on_hand": stock_level,
                "reorder_threshold": threshold,
                "is_out_of_stock": 1 if stock_level == 0 else 0
            })
    df_inventory = pd.DataFrame(inventory_records)

    # 5. Orders & Funnel Events
    print(f"Simulating {n_orders} orders and behavioral clickstream events...")
    order_records = []
    event_records = []
    event_id_counter = 1

    for i in range(n_orders):
        user_row = df_users.sample(1).iloc[0]
        uid = user_row["user_id"]
        group = user_row["experiment_group"]
        
        placed_time = fake.date_time_between(start_date=user_row["signup_at"], end_date='now')
        hour = placed_time.hour
        is_rush = 19 <= hour <= 22 or 8 <= hour <= 10
        session_id = f"SESS_{i:08d}"

        # Clickstream Funnel Progression
        event_records.append({
            "event_id": f"EVT_{event_id_counter:09d}",
            "session_id": session_id,
            "user_id": uid,
            "event_name": "search",
            "event_timestamp": placed_time - datetime.timedelta(minutes=np.random.randint(5, 15))
        })
        event_id_counter += 1

        # Search to Cart (~70% probability)
        converted_to_cart = np.random.rand() < 0.70
        if converted_to_cart:
            event_records.append({
                "event_id": f"EVT_{event_id_counter:09d}",
                "session_id": session_id,
                "user_id": uid,
                "event_name": "add_to_cart",
                "event_timestamp": placed_time - datetime.timedelta(minutes=np.random.randint(2, 5))
            })
            event_id_counter += 1

            # Cart to Checkout (~80% probability)
            converted_to_checkout = np.random.rand() < 0.80
            if converted_to_checkout:
                event_records.append({
                    "event_id": f"EVT_{event_id_counter:09d}",
                    "session_id": session_id,
                    "user_id": uid,
                    "event_name": "checkout_start",
                    "event_timestamp": placed_time - datetime.timedelta(minutes=1)
                })
                event_id_counter += 1

                # Pricing calculation based on A/B testing cohort
                if group == "control_flat_fee":
                    delivery_fee = 15.0
                    surge_fee = 0.0
                    drop_prob = 0.05
                else:
                    delivery_fee = 15.0
                    surge_fee = np.random.choice([20.0, 35.0, 50.0], p=[0.5, 0.35, 0.15]) if is_rush else 0.0
                    # Slight drop-off increase due to surge pricing elasticity
                    drop_prob = 0.12 if is_rush else 0.05

                # Checkout to Placed Order
                if np.random.rand() > drop_prob:
                    event_records.append({
                        "event_id": f"EVT_{event_id_counter:09d}",
                        "session_id": session_id,
                        "user_id": uid,
                        "event_name": "order_placed",
                        "event_timestamp": placed_time
                    })
                    event_id_counter += 1

                    # Order fulfillment metrics
                    base_delivery_time = np.random.normal(loc=17 if is_rush else 11, scale=3.5)
                    delivery_mins = max(5.0, round(base_delivery_time, 1))
                    sla_target = 12.0
                    order_val = round(np.random.exponential(scale=380) + 120, 2)

                    order_records.append({
                        "order_id": f"ORD_{i:08d}",
                        "user_id": uid,
                        "dark_store_id": np.random.choice(df_stores["dark_store_id"]),
                        "placed_at": placed_time,
                        "order_value": order_val,
                        "delivery_fee": delivery_fee,
                        "surge_fee": surge_fee,
                        "delivery_time_mins": delivery_mins,
                        "sla_target_mins": sla_target,
                        "status": np.random.choice(["delivered", "cancelled"], p=[0.97, 0.03])
                    })

    df_orders = pd.DataFrame(order_records)
    df_events = pd.DataFrame(event_records)

    return df_users, df_stores, df_skus, df_inventory, df_orders, df_events

if __name__ == "__main__":
    users, stores, skus, inventory, orders, events = generate_all_data(n_users=5000, n_orders=20000)
    print("Sample generation complete:")
    print(f"Users: {len(users)}, Orders: {len(orders)}, Events: {len(events)}")