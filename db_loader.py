import time
from sqlalchemy import create_engine, text
from config import DB_URI
from data_generator import generate_all_data

def init_db_and_load():
    engine = create_engine(DB_URI)
    print("Connecting to local SQLite database...")

    schema_sql = """
    DROP TABLE IF EXISTS fct_order_events;
    DROP TABLE IF EXISTS fct_inventory;
    DROP TABLE IF EXISTS fct_orders;
    DROP TABLE IF EXISTS dim_skus;
    DROP TABLE IF EXISTS dim_dark_stores;
    DROP TABLE IF EXISTS dim_users;

    CREATE TABLE dim_users (
        user_id TEXT PRIMARY KEY,
        signup_at TIMESTAMP NOT NULL,
        city_tier TEXT,
        acquisition_channel TEXT,
        experiment_group TEXT
    );

    CREATE TABLE dim_dark_stores (
        dark_store_id TEXT PRIMARY KEY,
        zone TEXT,
        capacity_orders_per_hr INTEGER
    );

    CREATE TABLE dim_skus (
        sku_id TEXT PRIMARY KEY,
        sku_name TEXT,
        category TEXT,
        cost_price REAL,
        selling_price REAL
    );

    CREATE TABLE fct_inventory (
        dark_store_id TEXT,
        sku_id TEXT,
        stock_on_hand INTEGER,
        reorder_threshold INTEGER,
        is_out_of_stock INTEGER,
        PRIMARY KEY (dark_store_id, sku_id)
    );

    CREATE TABLE fct_orders (
        order_id TEXT PRIMARY KEY,
        user_id TEXT,
        dark_store_id TEXT,
        placed_at TIMESTAMP NOT NULL,
        order_value REAL,
        delivery_fee REAL,
        surge_fee REAL,
        delivery_time_mins REAL,
        sla_target_mins REAL,
        status TEXT
    );

    CREATE TABLE fct_order_events (
        event_id TEXT PRIMARY KEY,
        session_id TEXT,
        user_id TEXT,
        event_name TEXT,
        event_timestamp TIMESTAMP NOT NULL
    );
    """

    with engine.begin() as conn:
        print("Creating tables...")
        for stmt in schema_sql.strip().split(';'):
            if stmt.strip():
                conn.execute(text(stmt))

    # Generate and Insert Data
    users, stores, skus, inventory, orders, events = generate_all_data(n_users=5000, n_orders=20000)

    print("Loading data into SQLite...")
    stores.to_sql("dim_dark_stores", engine, if_exists="append", index=False)
    users.to_sql("dim_users", engine, if_exists="append", index=False, chunksize=2000)
    skus.to_sql("dim_skus", engine, if_exists="append", index=False)
    inventory.to_sql("fct_inventory", engine, if_exists="append", index=False, chunksize=2000)
    orders.to_sql("fct_orders", engine, if_exists="append", index=False, chunksize=2000)
    events.to_sql("fct_order_events", engine, if_exists="append", index=False, chunksize=5000)

    print("Data ingestion complete. 'hyperlocal.db' created successfully!")

if __name__ == "__main__":
    init_db_and_load()