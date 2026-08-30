import os
import sys
from sqlalchemy import create_engine

# Add scripts directory to path to locate data_generator
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from data_generator import generate_all_data

DB_URI = os.getenv(
    "DATABASE_URL",
    "postgresql://hyperlocal_user:hyperlocal_pass@localhost:5432/hyperlocal_db"
)

def init_db_and_load():
    engine = create_engine(DB_URI)
    print("Connecting to PostgreSQL database...")

    users, stores, riders, skus, inventory, orders, events = generate_all_data(
        n_users=5000,
        n_orders=25000
    )

    print("Loading data into PostgreSQL tables...")
    stores.to_sql("dim_dark_stores", engine, if_exists="append", index=False)
    riders.to_sql("dim_riders", engine, if_exists="append", index=False)
    users.to_sql("dim_users", engine, if_exists="append", index=False, chunksize=2000)
    skus.to_sql("dim_skus", engine, if_exists="append", index=False)
    inventory.to_sql("fct_inventory", engine, if_exists="append", index=False, chunksize=2000)
    orders.to_sql("fct_orders", engine, if_exists="append", index=False, chunksize=2000)
    events.to_sql("fct_order_events", engine, if_exists="append", index=False, chunksize=5000)

    print("PostgreSQL data seeding complete!")

if __name__ == "__main__":
    init_db_and_load()