from typing import Optional, List, Dict, Any
import pandas as pd
from database.db import get_connection

# ----------------- Inventory Operations -----------------

def get_inventory(item_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve current inventory levels.
    Supports smart typo correction, fuzzy matching, and Bengali/Hindi transliteration lookups.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if item_name:
        from core.i18n import normalize_item_name
        norm = normalize_item_name(item_name)
        canonical = norm["canonical"]
        
        cursor.execute(
            """
            SELECT id, item_name, quantity, unit, category, last_updated 
            FROM inventory 
            WHERE item_name LIKE ? OR item_name LIKE ? OR item_name LIKE ?
            """,
            (f"%{item_name.strip()}%", f"%{canonical}%", f"%{canonical.split()[0]}%")
        )
    else:
        cursor.execute("SELECT id, item_name, quantity, unit, category, last_updated FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_inventory_item(item_name: str, quantity: float, unit: str, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Insert or update a single inventory item with smart normalization of typos
    and auto-inferred food categories.
    """
    from core.i18n import normalize_item_name
    norm = normalize_item_name(item_name)
    resolved_name = norm["canonical"] if norm["matched"] else item_name.strip().title()
    resolved_cat = (category.strip() if category and category.strip() != "None" else norm["category"]) or "Pantry"
    resolved_unit = unit.strip() if unit and unit.strip() != "None" else norm["default_unit"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventory (item_name, quantity, unit, category, last_updated)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(item_name) DO UPDATE SET
            quantity = excluded.quantity,
            unit = excluded.unit,
            category = excluded.category,
            last_updated = CURRENT_TIMESTAMP;
        """,
        (resolved_name, float(quantity), resolved_unit, resolved_cat)
    )
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "item_name": resolved_name,
        "quantity": float(quantity),
        "unit": resolved_unit,
        "category": resolved_cat,
        "display_bn": norm.get("display_bn", resolved_name),
        "display_hi": norm.get("display_hi", resolved_name),
        "message": f"Successfully added/updated {quantity} {resolved_unit} of '{resolved_name}' in inventory under category '{resolved_cat}'."
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
    conn.commit()
    conn.close()

def sync_inventory_from_dataframe(df: pd.DataFrame):
    """Save an entire modified dataframe from st.data_editor into the inventory table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory;")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO inventory (item_name, quantity, unit, category, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
            """,
            (str(row["item_name"]).strip(), float(row["quantity"]), str(row["unit"]).strip(), str(row["category"]).strip())
        )
    conn.commit()
    conn.close()

# ----------------- Supplier Operations -----------------

def get_supplier_details(supplier_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve contact details for suppliers matching the supplier name or category."""
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
    """Save an entire modified dataframe from st.data_editor into the suppliers table."""
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
    """Save an entire modified dataframe from st.data_editor into the orders table."""
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
    """Draft a purchase request requiring manager approval."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO purchase_requests (item_name, quantity, unit, supplier_name, status)
        VALUES (?, ?, ?, ?, 'PENDING_APPROVAL')
        """,
        (item_name.strip(), float(quantity), unit.strip(), supplier_name.strip())
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": request_id,
        "item_name": item_name,
        "quantity": quantity,
        "unit": unit,
        "supplier_name": supplier_name,
        "status": "PENDING_APPROVAL",
        "message": f"Draft purchase request #{request_id} created successfully. Awaiting approval in the Action Approvals tab."
    }

def get_pending_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests awaiting approval."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, quantity, unit, supplier_name, status, created_at FROM purchase_requests WHERE status = 'PENDING_APPROVAL' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests (pending, approved, rejected) for audit trail."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, quantity, unit, supplier_name, status, created_at, resolved_at FROM purchase_requests ORDER BY id DESC")
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
