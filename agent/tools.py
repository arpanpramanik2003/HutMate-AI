from typing import Optional, List, Dict, Any
import pandas as pd
from database.db import get_connection

# ----------------- Inventory Operations -----------------

def get_inventory(item_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve current inventory levels.
    Supports smart typo correction, fuzzy matching, and Bengali/Hindi transliteration lookups.
    Includes Par Levels, Unit Cost, Expiry Dates, and Low Stock Flags.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if item_name:
        from core.i18n import normalize_item_name
        norm = normalize_item_name(item_name)
        canonical = norm["canonical"]
        
        cursor.execute(
            """
            SELECT id, item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date, last_updated 
            FROM inventory 
            WHERE item_name LIKE ? OR item_name LIKE ? OR item_name LIKE ?
            """,
            (f"%{item_name.strip()}%", f"%{canonical}%", f"%{canonical.split()[0]}%")
        )
    else:
        cursor.execute("SELECT id, item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date, last_updated FROM inventory")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["min_par_level"] = float(d.get("min_par_level") or 5.0)
        d["cost_per_unit"] = float(d.get("cost_per_unit") or 0.0)
        d["expiry_date"] = str(d.get("expiry_date") or "")
        d["is_low_stock"] = d["quantity"] <= d["min_par_level"]
        result.append(d)
    return result

def upsert_inventory_item(
    item_name: str,
    quantity: float,
    unit: str,
    category: Optional[str] = None,
    min_par_level: Optional[float] = None,
    cost_per_unit: Optional[float] = None,
    expiry_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert or update a single inventory item with normalization,
    par levels, unit costs, and expiration dates.
    """
    from core.i18n import normalize_item_name
    norm = normalize_item_name(item_name)
    resolved_name = norm["canonical"] if norm["matched"] else item_name.strip().title()
    resolved_cat = (category.strip() if category and category.strip() != "None" else norm["category"]) or "Pantry"
    resolved_unit = unit.strip() if unit and unit.strip() != "None" else norm["default_unit"]
    resolved_par = float(min_par_level) if min_par_level is not None else 5.0
    resolved_cost = float(cost_per_unit) if cost_per_unit is not None else 0.0
    resolved_expiry = expiry_date.strip() if expiry_date else ""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventory (item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(item_name) DO UPDATE SET
            quantity = excluded.quantity,
            unit = excluded.unit,
            category = excluded.category,
            min_par_level = CASE WHEN excluded.min_par_level > 0 THEN excluded.min_par_level ELSE inventory.min_par_level END,
            cost_per_unit = CASE WHEN excluded.cost_per_unit > 0 THEN excluded.cost_per_unit ELSE inventory.cost_per_unit END,
            expiry_date = CASE WHEN excluded.expiry_date != '' THEN excluded.expiry_date ELSE inventory.expiry_date END,
            last_updated = CURRENT_TIMESTAMP;
        """,
        (resolved_name, float(quantity), resolved_unit, resolved_cat, resolved_par, resolved_cost, resolved_expiry)
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "item_name": resolved_name,
        "quantity": float(quantity),
        "unit": resolved_unit,
        "category": resolved_cat,
        "min_par_level": resolved_par,
        "cost_per_unit": resolved_cost,
        "expiry_date": resolved_expiry,
        "is_low_stock": float(quantity) <= resolved_par,
        "display_bn": norm.get("display_bn", resolved_name),
        "display_hi": norm.get("display_hi", resolved_name),
        "message": f"Successfully added/updated {quantity} {resolved_unit} of '{resolved_name}' in inventory."
    }

def delete_inventory_item(identifier: Any) -> Dict[str, Any]:
    """Delete an item from inventory by its ID (int) or item_name (str)."""
    conn = get_connection()
    cursor = conn.cursor()
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        cursor.execute("DELETE FROM inventory WHERE id = ?", (int(identifier),))
    else:
        cursor.execute("DELETE FROM inventory WHERE item_name LIKE ?", (f"%{str(identifier).strip()}%",))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "deleted_count": count,
        "message": f"Deleted {count} inventory item(s) matching '{identifier}'."
    }

def sync_inventory_from_dataframe(df: pd.DataFrame):
    """Save modified dataframe into inventory table while preserving par levels & costs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory;")
    for _, row in df.iterrows():
        min_par = float(row.get("min_par_level", 5.0)) if pd.notnull(row.get("min_par_level")) else 5.0
        cost = float(row.get("cost_per_unit", 0.0)) if pd.notnull(row.get("cost_per_unit")) else 0.0
        expiry = str(row.get("expiry_date", "")).strip() if pd.notnull(row.get("expiry_date")) else ""
        cursor.execute(
            """
            INSERT INTO inventory (item_name, quantity, unit, category, min_par_level, cost_per_unit, expiry_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """,
            (
                str(row["item_name"]).strip(),
                float(row["quantity"]),
                str(row["unit"]).strip(),
                str(row["category"]).strip(),
                min_par,
                cost,
                expiry,
            )
        )
    conn.commit()
    conn.close()

def get_low_stock_alerts() -> List[Dict[str, Any]]:
    """
    Find all inventory items currently at or below their minimum par level.
    Calculates shortfall and estimated restock costs.
    """
    items = get_inventory()
    alerts = []
    for item in items:
        if item["quantity"] <= item["min_par_level"]:
            shortfall = max(0.0, item["min_par_level"] - item["quantity"])
            est_restock = round(shortfall * item["cost_per_unit"], 2)
            alerts.append({
                "id": item["id"],
                "item_name": item["item_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "min_par_level": item["min_par_level"],
                "shortfall": shortfall,
                "cost_per_unit": item["cost_per_unit"],
                "estimated_restock_cost": est_restock,
                "expiry_date": item["expiry_date"],
                "message": f"CRITICAL: '{item['item_name']}' is at {item['quantity']} {item['unit']} (Par level: {item['min_par_level']} {item['unit']}). Shortfall: {shortfall} {item['unit']}."
            })
    return alerts

# ----------------- Supplier Operations -----------------

def get_supplier_details(supplier_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve contact details for suppliers matching supplier name or category."""
    conn = get_connection()
    cursor = conn.cursor()
    if supplier_name:
        cursor.execute(
            "SELECT id, name, contact_person, phone, email, supplied_categories FROM suppliers WHERE name LIKE ? OR supplied_categories LIKE ?",
            (f"%{supplier_name}%", f"%{supplier_name}%")
        )
    else:
        cursor.execute("SELECT id, name, contact_person, phone, email, supplied_categories FROM suppliers")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_supplier(name: str, contact_person: str, phone: str, email: str, supplied_categories: str):
    """Insert or update a supplier."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO suppliers (name, contact_person, phone, email, supplied_categories)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            contact_person = excluded.contact_person,
            phone = excluded.phone,
            email = excluded.email,
            supplied_categories = excluded.supplied_categories;
        """,
        (name.strip(), contact_person.strip(), phone.strip(), email.strip(), supplied_categories.strip())
    )
    conn.commit()
    conn.close()

def delete_supplier(supplier_id: int):
    """Delete a supplier by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit()
    conn.close()

def sync_suppliers_from_dataframe(df: pd.DataFrame):
    """Save an entire modified dataframe into the suppliers table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM suppliers;")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO suppliers (name, contact_person, phone, email, supplied_categories)
            VALUES (?, ?, ?, ?, ?);
            """,
            (str(row["name"]).strip(), str(row["contact_person"]).strip(), str(row["phone"]).strip(), str(row["email"]).strip(), str(row["supplied_categories"]).strip())
        )
    conn.commit()
    conn.close()

# ----------------- Order Operations -----------------

def get_orders() -> List[Dict[str, Any]]:
    """Retrieve all current orders."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, order_number, item_name, quantity, unit, supplier_name, status, order_date FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_order_status(order_number: str) -> Optional[Dict[str, Any]]:
    """Retrieve current status and details of an order by order number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, order_number, item_name, quantity, unit, supplier_name, status, order_date FROM orders WHERE order_number = ?",
        (order_number.strip().upper(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_order(order_number: str, item_name: str, quantity: float, unit: str, supplier_name: str, status: str):
    """Insert or update an order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (order_number, item_name, quantity, unit, supplier_name, status, order_date)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(order_number) DO UPDATE SET
            item_name = excluded.item_name,
            quantity = excluded.quantity,
            unit = excluded.unit,
            supplier_name = excluded.supplier_name,
            status = excluded.status;
        """,
        (order_number.strip().upper(), item_name.strip(), float(quantity), unit.strip(), supplier_name.strip(), status.strip().upper())
    )
    conn.commit()
    conn.close()

def delete_order(order_id: int):
    """Delete an order by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def sync_orders_from_dataframe(df: pd.DataFrame):
    """Save an entire modified dataframe into the orders table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders;")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO orders (order_number, item_name, quantity, unit, supplier_name, status, order_date)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """,
            (str(row["order_number"]).strip().upper(), str(row["item_name"]).strip(), float(row["quantity"]), str(row["unit"]).strip(), str(row["supplier_name"]).strip(), str(row["status"]).strip().upper())
        )
    conn.commit()
    conn.close()

# ----------------- Purchase Request Lifecycle -----------------

def create_purchase_request(item_name: str, quantity: float, unit: str, supplier_name: str) -> Dict[str, Any]:
    """
    Draft a purchase request requiring manager approval.
    Automatically calculates estimated cost from inventory unit cost.
    """
    from core.i18n import normalize_item_name
    norm = normalize_item_name(item_name)
    resolved_name = norm["canonical"] if norm["matched"] else item_name.strip().title()

    # Look up item's unit cost in inventory
    inv_items = get_inventory(resolved_name)
    cost_per_unit = inv_items[0]["cost_per_unit"] if inv_items else 0.0
    estimated_cost = round(float(quantity) * cost_per_unit, 2)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO purchase_requests (item_name, quantity, unit, supplier_name, estimated_cost, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING_APPROVAL')
        """,
        (resolved_name, float(quantity), unit.strip(), supplier_name.strip(), estimated_cost)
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    cost_str = f"₹{estimated_cost:,.2f}" if estimated_cost > 0 else "Pending quote"
    return {
        "id": request_id,
        "item_name": resolved_name,
        "quantity": quantity,
        "unit": unit,
        "supplier_name": supplier_name,
        "estimated_cost": estimated_cost,
        "status": "PENDING_APPROVAL",
        "message": f"Draft purchase request #{request_id} created for {quantity} {unit} of '{resolved_name}' ({cost_str}). Awaiting approval."
    }

def get_pending_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests awaiting approval."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, quantity, unit, supplier_name, estimated_cost, status, created_at FROM purchase_requests WHERE status = 'PENDING_APPROVAL' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests (pending, approved, rejected) for audit trail."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, quantity, unit, supplier_name, estimated_cost, status, created_at, resolved_at FROM purchase_requests ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_purchase_request(request_id: int, decision: str) -> bool:
    """
    Approve or reject a pending purchase request ('APPROVED' or 'REJECTED').
    When approved:
    1. Updates request status to 'APPROVED'.
    2. Increments inventory quantity for the item.
    3. Automatically records a new confirmed order in the orders table.
    """
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Decision must be either 'APPROVED' or 'REJECTED'")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE purchase_requests
        SET status = ?, resolved_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'PENDING_APPROVAL'
        """,
        (decision, request_id)
    )
    updated = cursor.rowcount > 0

    if updated and decision == "APPROVED":
        cursor.execute("SELECT item_name, quantity, unit, supplier_name FROM purchase_requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        if row:
            item_name = row["item_name"]
            qty = row["quantity"]
            unit = row["unit"]
            supplier = row["supplier_name"]

            # 1. Update live stock in inventory
            cursor.execute(
                """
                INSERT INTO inventory (item_name, quantity, unit, category, last_updated)
                VALUES (?, ?, ?, 'Pantry', CURRENT_TIMESTAMP)
                ON CONFLICT(item_name) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    last_updated = CURRENT_TIMESTAMP;
                """,
                (item_name, qty, unit)
            )

            # 2. Record new official order record
            order_code = f"ORD-APR{request_id:04d}"
            cursor.execute(
                """
                INSERT INTO orders (order_number, item_name, quantity, unit, supplier_name, status, order_date)
                VALUES (?, ?, ?, ?, ?, 'PROCESSING', CURRENT_TIMESTAMP);
                """,
                (order_code, item_name, qty, unit, supplier)
            )

    conn.commit()
    conn.close()
    return updated

# ----------------- Kitchen Bill of Materials (BOM) & Recipes -----------------

def get_recipes(dish_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve restaurant recipes with ingredients (Bill of Materials)."""
    conn = get_connection()
    cursor = conn.cursor()

    if dish_name:
        cursor.execute(
            "SELECT id, dish_name, category, portion_description, instructions FROM recipes WHERE dish_name LIKE ?",
            (f"%{dish_name.strip()}%",)
        )
    else:
        cursor.execute("SELECT id, dish_name, category, portion_description, instructions FROM recipes")
    
    recipe_rows = cursor.fetchall()
    recipes = []
    for r in recipe_rows:
        rec_id = r["id"]
        cursor.execute(
            "SELECT ingredient_name, quantity_per_portion, unit FROM recipe_ingredients WHERE recipe_id = ?",
            (rec_id,)
        )
        ing_rows = cursor.fetchall()
        recipes.append({
            "id": rec_id,
            "dish_name": r["dish_name"],
            "category": r["category"],
            "portion_description": r["portion_description"],
            "instructions": r["instructions"],
            "ingredients": [dict(i) for i in ing_rows]
        })

    conn.close()
    return recipes

def check_dish_feasibility(dish_name: str) -> Dict[str, Any]:
    """
    Calculate how many portions of a dish can be prepared with current inventory stock.
    Identifies the bottleneck (limiting ingredient).
    """
    recipes = get_recipes(dish_name)
    if not recipes:
        return {
            "status": "error",
            "message": f"Recipe for '{dish_name}' not found in master cookbook."
        }
    
    recipe = recipes[0]
    ingredients = recipe["ingredients"]
    if not ingredients:
        return {
            "status": "error",
            "message": f"No ingredients configured for '{recipe['dish_name']}'."
        }

    feasibility_breakdown = []
    max_portions = float("inf")
    limiting_ingredient = None

    for ing in ingredients:
        name = ing["ingredient_name"]
        needed_per_portion = float(ing["quantity_per_portion"])
        inv = get_inventory(name)
        current_stock = inv[0]["quantity"] if inv else 0.0

        if needed_per_portion > 0:
            portions_from_this = current_stock / needed_per_portion
        else:
            portions_from_this = float("inf")

        if portions_from_this < max_portions:
            max_portions = portions_from_this
            limiting_ingredient = name

        feasibility_breakdown.append({
            "ingredient": name,
            "needed_per_portion": needed_per_portion,
            "unit": ing["unit"],
            "current_stock": current_stock,
            "possible_portions": round(portions_from_this, 1)
        })

    max_portions = 0 if max_portions == float("inf") else int(max_portions)

    return {
        "status": "success",
        "dish_name": recipe["dish_name"],
        "max_portions_possible": max_portions,
        "limiting_ingredient": limiting_ingredient,
        "ingredients_breakdown": feasibility_breakdown,
        "message": f"You can currently prepare {max_portions} portion(s) of '{recipe['dish_name']}'. Bottleneck ingredient: {limiting_ingredient}."
    }

def record_dish_sales(dish_name: str, portions: float) -> Dict[str, Any]:
    """
    Deduct inventory ingredients required to prepare/sell specified portions of a dish.
    Validates stock availability and records transaction in kitchen_sales_log.
    """
    if portions <= 0:
        return {"status": "error", "message": "Portions must be greater than zero."}

    recipes = get_recipes(dish_name)
    if not recipes:
        return {"status": "error", "message": f"Recipe for '{dish_name}' not found."}
    
    recipe = recipes[0]
    ingredients = recipe["ingredients"]

    # 1. Pre-flight stock availability check
    shortages = []
    deduction_plan = []
    for ing in ingredients:
        name = ing["ingredient_name"]
        total_needed = float(ing["quantity_per_portion"]) * float(portions)
        inv = get_inventory(name)
        current_stock = inv[0]["quantity"] if inv else 0.0

        if current_stock < total_needed:
            shortages.append(
                f"'{name}' (need {total_needed:.2f} {ing['unit']}, have {current_stock:.2f} {ing['unit']})"
            )
        deduction_plan.append((name, total_needed, ing["unit"]))

    if shortages:
        return {
            "status": "insufficient_stock",
            "dish_name": recipe["dish_name"],
            "requested_portions": portions,
            "shortages": shortages,
            "message": f"Cannot fulfill {portions} portions of '{recipe['dish_name']}'. Insufficient stock for: {', '.join(shortages)}."
        }

    # 2. Execute atomic stock deduction
    conn = get_connection()
    cursor = conn.cursor()
    deduction_strings = []

    for name, qty_deduct, unit in deduction_plan:
        cursor.execute(
            """
            UPDATE inventory
            SET quantity = quantity - ?, last_updated = CURRENT_TIMESTAMP
            WHERE item_name = ?
            """,
            (qty_deduct, name)
        )
        deduction_strings.append(f"{qty_deduct:.2f} {unit} {name}")

    summary_text = f"Prepared {portions}x {recipe['dish_name']} (Deducted: {', '.join(deduction_strings)})"
    cursor.execute(
        "INSERT INTO kitchen_sales_log (dish_name, portions, deductions_summary) VALUES (?, ?, ?);",
        (recipe["dish_name"], portions, summary_text)
    )

    conn.commit()
    conn.close()

    # 3. Check for low stock warnings after deduction
    post_alerts = [a for a in get_low_stock_alerts() if any(p[0] == a["item_name"] for p in deduction_plan)]

    return {
        "status": "success",
        "dish_name": recipe["dish_name"],
        "portions_prepared": portions,
        "deductions": deduction_strings,
        "low_stock_warnings": [a["message"] for a in post_alerts],
        "message": f"Successfully deducted ingredients for {portions}x '{recipe['dish_name']}'. Inventory updated."
    }

def get_kitchen_sales_log(limit: int = 15) -> List[Dict[str, Any]]:
    """Retrieve recent kitchen production and dish sales deductions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, dish_name, portions, deductions_summary, logged_at FROM kitchen_sales_log ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
