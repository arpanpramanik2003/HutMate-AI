from database.db import get_connection, init_db

def seed_sample_data():
    """Populate demonstration data for restaurant inventory, suppliers, and orders."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing demo data
    cursor.execute("DELETE FROM inventory;")
    cursor.execute("DELETE FROM suppliers;")
    cursor.execute("DELETE FROM orders;")

    # Seed Inventory
    sample_inventory = [
        ("Chicken Breast", 14.5, "kg", "Poultry"),
        ("Basmati Rice", 50.0, "kg", "Grains"),
        ("Cooking Oil", 25.0, "liters", "Pantry"),
        ("Yellow Onions", 18.0, "kg", "Produce"),
        ("Tomatoes", 8.5, "kg", "Produce"),
        ("Garam Masala", 3.0, "kg", "Spices"),
        ("Yogurt", 6.0, "kg", "Dairy"),
    ]
    cursor.executemany(
        "INSERT INTO inventory (item_name, quantity, unit, category) VALUES (?, ?, ?, ?);",
        sample_inventory,
    )

    # Seed Suppliers
    sample_suppliers = [
        ("ABC Foods Ltd", "Rajesh Sharma", "+91 98765 43210", "orders@abcfoods.com", "Poultry, Meat, Dairy"),
        ("Golden Grain Traders", "Anil Mehta", "+91 98111 22334", "sales@goldengrain.com", "Grains, Spices, Pantry"),
        ("Fresh Farm Produce", "Sunita Rao", "+91 98222 33445", "contact@freshfarm.com", "Produce, Vegetables"),
    ]
    cursor.executemany(
        "INSERT INTO suppliers (name, contact_person, phone, email, supplied_categories) VALUES (?, ?, ?, ?, ?);",
        sample_suppliers,
    )

    # Seed Orders
    sample_orders = [
        ("ORD-1001", "Basmati Rice", 100.0, "kg", "Golden Grain Traders", "DELIVERED"),
        ("ORD-1002", "Chicken Breast", 30.0, "kg", "ABC Foods Ltd", "IN_TRANSIT"),
        ("ORD-1003", "Cooking Oil", 50.0, "liters", "Golden Grain Traders", "PROCESSING"),
    ]
    cursor.executemany(
        "INSERT INTO orders (order_number, item_name, quantity, unit, supplier_name, status) VALUES (?, ?, ?, ?, ?, ?);",
        sample_orders,
    )

    conn.commit()
    conn.close()
    print("Demo data seeded successfully.")

if __name__ == "__main__":
    seed_sample_data()

