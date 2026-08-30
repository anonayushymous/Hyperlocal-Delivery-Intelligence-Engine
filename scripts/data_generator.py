import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

def generate_all_data(n_users=5000, n_orders=25000):
    start_date = datetime.now() - timedelta(days=60)
    
    # 1. Dark Stores with Real Geocoordinates (Mumbai area mock)
    stores_data = [
        {"dark_store_id": "DS_01", "zone": "Bandra West", "capacity_orders_per_hr": 220, "lat": 19.0596, "lon": 72.8295},
        {"dark_store_id": "DS_02", "zone": "Andheri East", "capacity_orders_per_hr": 350, "lat": 19.1136, "lon": 72.8697},
        {"dark_store_id": "DS_03", "zone": "Koramangala", "capacity_orders_per_hr": 300, "lat": 12.9352, "lon": 77.6245},
        {"dark_store_id": "DS_04", "zone": "Indiranagar", "capacity_orders_per_hr": 280, "lat": 12.9784, "lon": 77.6408},
        {"dark_store_id": "DS_05", "zone": "Cyber Hub", "capacity_orders_per_hr": 400, "lat": 28.4950, "lon": 77.0895},
        {"dark_store_id": "DS_06", "zone": "Powai Hub", "capacity_orders_per_hr": 250, "lat": 19.1176, "lon": 72.9060},
        {"dark_store_id": "DS_07", "zone": "Whitefield", "capacity_orders_per_hr": 320, "lat": 12.9698, "lon": 77.7500}
    ]
    df_stores = pd.DataFrame(stores_data)

    # 2. Riders Fleet
    riders_data = []
    for i in range(1, 151):
        riders_data.append({
            "rider_id": f"RIDER_{i:03d}",
            "dark_store_id": random.choice(df_stores["dark_store_id"].tolist()),
            "rating": round(random.uniform(4.2, 5.0), 2),
            "vehicle_type": random.choice(["Electric Scooter", "Motorcycle", "Bicycle"])
        })
    df_riders = pd.DataFrame(riders_data)

    # 3. Users
    users = []
    for i in range(1, n_users + 1):
        users.append({
            "user_id": f"USR_{i:05d}",
            "signup_at": start_date + timedelta(days=random.randint(0, 30)),
            "city_tier": random.choices(["Tier 1", "Tier 2"], weights=[0.75, 0.25])[0],
            "experiment_group": random.choice(["control", "treatment"])
        })
    df_users = pd.DataFrame(users)

    # 4. SKUs
    categories = {
        "Dairy & Bread": [("Amul Butter 100g", 55, 60), ("Nandini Milk 500ml", 24, 28), ("Brown Bread 400g", 40, 50)],
        "Fresh Vegetables": [("Farm Potatoes 1kg", 25, 35), ("Red Onions 1kg", 30, 45), ("Tomatoes 500g", 20, 30)],
        "Snacks & Munchies": [("Lay's Chips Classic", 15, 20), ("Kurkure Masala", 15, 20), ("Almonds 200g", 140, 190)],
        "Instant Food": [("Maggi 4-Pack", 48, 56), ("Cup Noodles", 38, 50)]
    }
    skus = []
    sku_id = 1
    for cat, items in categories.items():
        for name, cost, sell in items:
            skus.append({"sku_id": f"SKU_{sku_id:03d}", "sku_name": name, "category": cat, "cost_price": cost, "selling_price": sell})
            sku_id += 1
    df_skus = pd.DataFrame(skus)

    # 5. Inventory
    inventory = []
    for store_id in df_stores["dark_store_id"]:
        for sku in df_skus["sku_id"]:
            stock = random.choices([0, random.randint(1, 5), random.randint(15, 60)], weights=[0.05, 0.15, 0.80])[0]
            inventory.append({
                "dark_store_id": store_id,
                "sku_id": sku,
                "stock_on_hand": stock,
                "reorder_threshold": 10,
                "is_out_of_stock": 1 if stock == 0 else 0
            })
    df_inventory = pd.DataFrame(inventory)

    # 6. Orders with Failures, Delivery Times, and Complaints
    orders = []
    events = []
    failure_reasons = ["Customer Not Reachable", "Incorrect Address", "Rider Vehicle Breakdown", "Item Damaged in Transit", "Customer Cancelled Late"]
    complaint_types = ["Late Delivery (>15m)", "Missing Item", "Damaged Packaging", "Rider Behavior", "Wrong Item Delivered"]
    
    for i in range(1, n_orders + 1):
        user = random.choice(users)
        store = random.choice(stores_data)
        rider = random.choice(df_riders[df_riders["dark_store_id"] == store["dark_store_id"]].to_dict('records') or riders_data)
        
        order_time = start_date + timedelta(days=random.randint(0, 59), hours=random.randint(6, 23), minutes=random.randint(0, 59))
        is_rush_hour = order_time.hour in [8, 9, 10, 19, 20, 21, 22]
        
        # Treatment vs Control Pricing
        if user["experiment_group"] == "treatment" and is_rush_hour:
            surge_fee = random.choice([25.0, 35.0, 50.0])
            base_basket = np.random.gamma(shape=5.0, scale=80.0) + 30.0
        else:
            surge_fee = 0.0
            base_basket = np.random.gamma(shape=4.8, scale=75.0)

        # Status: 94% Delivered, 6% Failed
        status = random.choices(["delivered", "failed", "cancelled"], weights=[0.94, 0.04, 0.02])[0]
        failure_reason = random.choice(failure_reasons) if status != "delivered" else None
        
        # Delivery Time Distribution (Log-normal bell curve around 11 mins)
        del_time = float(np.random.lognormal(mean=2.35, sigma=0.32)) if status == "delivered" else None
        
        # Customer Complaints (5% of delivered orders lodge a complaint)
        has_complaint = (random.random() < 0.05) if status == "delivered" else False
        complaint_reason = random.choice(complaint_types) if has_complaint else None

        order_id = f"ORD_{i:06d}"
        orders.append({
            "order_id": order_id,
            "user_id": user["user_id"],
            "dark_store_id": store["dark_store_id"],
            "rider_id": rider["rider_id"],
            "placed_at": order_time,
            "order_value": round(base_basket, 2),
            "delivery_fee": 15.0,
            "surge_fee": surge_fee,
            "delivery_time_mins": round(del_time, 1) if del_time else None,
            "sla_target_mins": 12.0,
            "status": status,
            "failure_reason": failure_reason,
            "complaint_reason": complaint_reason
        })

        # Clickstream Funnel Events
        session_id = f"SESS_{i:06d}"
        events.append({"event_id": f"EV_{i}_1", "session_id": session_id, "user_id": user["user_id"], "event_name": "search", "event_timestamp": order_time - timedelta(minutes=6)})
        events.append({"event_id": f"EV_{i}_2", "session_id": session_id, "user_id": user["user_id"], "event_name": "add_to_cart", "event_timestamp": order_time - timedelta(minutes=4)})
        if random.random() < 0.85:
            events.append({"event_id": f"EV_{i}_3", "session_id": session_id, "user_id": user["user_id"], "event_name": "checkout_start", "event_timestamp": order_time - timedelta(minutes=2)})
            if random.random() < 0.90:
                events.append({"event_id": f"EV_{i}_4", "session_id": session_id, "user_id": user["user_id"], "event_name": "order_placed", "event_timestamp": order_time})

    return df_users, df_stores, df_riders, df_skus, df_inventory, pd.DataFrame(orders), pd.DataFrame(events)