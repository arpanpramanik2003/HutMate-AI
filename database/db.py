import sqlite3
from pathlib import Path
from core import config

def get_connection() -> sqlite3.Connection:
    """Return an active connection to the SQLite database with dictionary-like row access."""
    Path(config.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the operational tables for inventory, orders, suppliers, recipes, and purchase requests."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Inventory Items (with Par Levels, Costs, and Expiry Dates)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        category TEXT NOT NULL,
        min_par_level REAL DEFAULT 5.0,
        cost_per_unit REAL DEFAULT 0.0,
        expiry_date TEXT DEFAULT '',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check for existing table schema migrations
    cursor.execute("PRAGMA table_info(inventory);")
    existing_cols = [row["name"] for row in cursor.fetchall()]
    if "min_par_level" not in existing_cols:
        cursor.execute("ALTER TABLE inventory ADD COLUMN min_par_level REAL DEFAULT 5.0;")
    if "cost_per_unit" not in existing_cols:
        cursor.execute("ALTER TABLE inventory ADD COLUMN cost_per_unit REAL DEFAULT 0.0;")
    if "expiry_date" not in existing_cols:
        cursor.execute("ALTER TABLE inventory ADD COLUMN expiry_date TEXT DEFAULT '';")

    # 2. Suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        supplied_categories TEXT
    );
    """)

    # 3. Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        item_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        status TEXT NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Action Requests / Purchase Approvals (with Estimated Cost)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        estimated_cost REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
        requested_by TEXT DEFAULT 'HutMate Agent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    );
    """)

    cursor.execute("PRAGMA table_info(purchase_requests);")
    pr_cols = [row["name"] for row in cursor.fetchall()]
    if "estimated_cost" not in pr_cols:
        cursor.execute("ALTER TABLE purchase_requests ADD COLUMN estimated_cost REAL DEFAULT 0.0;")

    # 5. Master Menu & Recipes (Bill of Materials)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dish_name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        portion_description TEXT DEFAULT '1 portion',
        instructions TEXT DEFAULT ''
    );
    """)

    # 6. Recipe Ingredients (Consumption Ratios)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        ingredient_name TEXT NOT NULL,
        quantity_per_portion REAL NOT NULL,
        unit TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
    );
    """)

    # 7. Kitchen Sales & Production Consumption Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kitchen_sales_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dish_name TEXT NOT NULL,
        portions REAL NOT NULL,
        deductions_summary TEXT NOT NULL,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema initialized successfully.")
