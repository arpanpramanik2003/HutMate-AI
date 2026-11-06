from database.db import get_connection, init_db

def seed_sample_data():
    """Populate demonstration data for restaurant inventory, suppliers, orders, and recipes."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing demo data
    cursor.execute("DELETE FROM inventory;")
    cursor.execute("DELETE FROM suppliers;")
    cursor.execute("DELETE FROM orders;")
    cursor.execute("DELETE FROM recipes;")
    cursor.execute("DELETE FROM recipe_ingredients;")
    cursor.execute("DELETE FROM kitchen_sales_log;")

    # Seed Inventory (item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date)
    sample_inventory = [
        ("Chicken Breast", 14.5, "kg", "Poultry", 10.0, 240.0, "2026-11-12"),
        ("Basmati Rice", 50.0, "kg", "Grains", 25.0, 95.0, "2027-05-20"),
        ("Cooking Oil", 25.0, "liters", "Pantry", 15.0, 140.0, "2027-02-28"),
        ("Yellow Onions", 18.0, "kg", "Produce", 12.0, 45.0, "2026-11-25"),
        ("Tomatoes", 8.5, "kg", "Produce", 10.0, 50.0, "2026-11-14"),        # Below Par Level
        ("Garam Masala", 3.0, "kg", "Spices", 2.0, 450.0, "2027-08-30"),
        ("Yogurt", 6.0, "kg", "Dairy", 8.0, 70.0, "2026-11-15"),             # Below Par Level
        ("Cheese", 4.0, "packets", "Dairy", 10.0, 120.0, "2026-11-20"),      # Below Par Level
        ("Wheat Flour (Atta)", 35.0, "kg", "Grains", 20.0, 42.0, "2027-04-10"),
        ("Butter", 7.5, "kg", "Dairy", 5.0, 480.0, "2026-12-10"),
        ("Garlic", 4.0, "kg", "Produce", 3.0, 160.0, "2026-11-30"),
        ("Ginger", 3.5, "kg", "Produce", 3.0, 150.0, "2026-11-30"),
    ]
    cursor.executemany(
        """
        INSERT INTO inventory (item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
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

    # Seed Master Menu Recipes (Bill of Materials)
    sample_recipes = [
        ("Dum Chicken Biryani", "Main Course", "1 portion (serves 1)", "Marinate chicken in yogurt and spices. Layer with 70% parboiled rice and slow dum cook for 30 mins."),
        ("Paneer Butter Masala", "Main Course", "1 portion (serves 1)", "Simmer pureed tomatoes, butter, and cashew gravy. Fold in paneer cubes gently."),
        ("Garlic Butter Naan", "Breads", "1 piece", "Roll dough, apply minced garlic and fresh coriander, bake in clay tandoor and brush with melted butter.")
    ]
    for dish_name, category, portion_desc, instructions in sample_recipes:
        cursor.execute(
            "INSERT INTO recipes (dish_name, category, portion_description, instructions) VALUES (?, ?, ?, ?);",
            (dish_name, category, portion_desc, instructions)
        )
        recipe_id = cursor.lastrowid

        if dish_name == "Dum Chicken Biryani":
            ingredients = [
                ("Chicken Breast", 0.25, "kg"),
                ("Basmati Rice", 0.20, "kg"),
                ("Yogurt", 0.075, "kg"),
                ("Yellow Onions", 0.06, "kg"),
                ("Cooking Oil", 0.025, "liters"),
                ("Garam Masala", 0.008, "kg")
            ]
        elif dish_name == "Paneer Butter Masala":
            ingredients = [
                ("Cheese", 0.25, "packets"),
                ("Tomatoes", 0.20, "kg"),
                ("Butter", 0.04, "kg"),
                ("Garam Masala", 0.008, "kg")
            ]
        elif dish_name == "Garlic Butter Naan":
            ingredients = [
                ("Wheat Flour (Atta)", 0.12, "kg"),
                ("Yogurt", 0.03, "kg"),
                ("Butter", 0.025, "kg"),
                ("Garlic", 0.015, "kg")
            ]
        else:
            ingredients = []

        for ing_name, qty, unit in ingredients:
            cursor.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, ingredient_name, quantity_per_portion, unit)
                VALUES (?, ?, ?, ?);
                """,
                (recipe_id, ing_name, qty, unit)
            )

    conn.commit()
    conn.close()
    print("Demo data seeded successfully with Recipes and Par Levels.")

if __name__ == "__main__":
    seed_sample_data()
