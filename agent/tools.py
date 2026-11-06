from typing import Optional, List, Dict, Any
import pandas as pd
from database.repositories import (
    InventoryRepository,
    RecipesRepository,
    SuppliersRepository,
    OrdersRepository,
    ApprovalsRepository,
)

# Repository singletons for tool execution
_inv_repo = InventoryRepository()
_recipes_repo = RecipesRepository()
_suppliers_repo = SuppliersRepository()
_orders_repo = OrdersRepository()
_approvals_repo = ApprovalsRepository()

# ----------------- Inventory Operations -----------------

def get_inventory(item_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve current inventory levels.
    Supports smart typo correction, fuzzy matching, and Bengali/Hindi transliteration lookups.
    Includes Par Levels, Unit Cost, Expiry Dates, and Low Stock Flags.
    """
    return _inv_repo.get_all(item_name)

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
    return _inv_repo.upsert(
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        category=category,
        min_par_level=min_par_level,
        cost_per_unit=cost_per_unit,
        expiry_date=expiry_date,
    )

def delete_inventory_item(identifier: Any) -> Dict[str, Any]:
    """Delete an item from inventory by its ID (int) or item_name (str)."""
    count = _inv_repo.delete(identifier)
    return {
        "status": "success",
        "deleted_count": count,
        "message": f"Deleted {count} inventory item(s) matching '{identifier}'."
    }

def sync_inventory_from_dataframe(df: pd.DataFrame):
    """Save modified dataframe into inventory table while preserving par levels & costs."""
    _inv_repo.sync_all(df.to_dict(orient="records"))

def get_low_stock_alerts() -> List[Dict[str, Any]]:
    """
    Find all inventory items currently at or below their minimum par level.
    Calculates shortfall and estimated restock costs.
    """
    return _inv_repo.get_low_stock()

# ----------------- Supplier Operations -----------------

def get_supplier_details(supplier_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve contact details for suppliers matching supplier name or category."""
    return _suppliers_repo.get_all(supplier_name)

def upsert_supplier(name: str, contact_person: str = "", phone: str = "", email: str = "", supplied_categories: str = ""):
    """Insert or update a supplier."""
    return _suppliers_repo.upsert(
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        supplied_categories=supplied_categories,
    )

def delete_supplier(supplier_id: int):
    """Delete a supplier by ID."""
    return _suppliers_repo.delete(supplier_id)

def sync_suppliers_from_dataframe(df: pd.DataFrame):
    """Save an entire modified dataframe into the suppliers table."""
    _suppliers_repo.sync_all(df.to_dict(orient="records"))

# ----------------- Order Operations -----------------

def get_orders() -> List[Dict[str, Any]]:
    """Retrieve all current orders."""
    return _orders_repo.get_all()

def get_order_status(order_number: str) -> Optional[Dict[str, Any]]:
    """Retrieve current status and details of an order by order number."""
    return _orders_repo.get_by_order_number(order_number)

def upsert_order(order_number: str, item_name: str, quantity: float, unit: str, supplier_name: str, status: str):
    """Insert or update an order."""
    return _orders_repo.upsert(
        order_number=order_number,
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        supplier_name=supplier_name,
        status=status,
    )

def delete_order(order_id: int):
    """Delete an order by ID."""
    return _orders_repo.delete(order_id)

def sync_orders_from_dataframe(df: pd.DataFrame):
    """Save an entire modified dataframe into the orders table."""
    _orders_repo.sync_all(df.to_dict(orient="records"))

# ----------------- Purchase Request Lifecycle -----------------

def create_purchase_request(item_name: str, quantity: float, unit: str, supplier_name: str) -> Dict[str, Any]:
    """
    Draft a purchase request requiring manager approval.
    Automatically calculates estimated cost from inventory unit cost.
    """
    return _approvals_repo.create_draft(
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        supplier_name=supplier_name,
    )

def get_pending_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests awaiting approval."""
    return _approvals_repo.get_pending()

def get_all_purchase_requests() -> List[Dict[str, Any]]:
    """List all purchase requests (pending, approved, rejected) for audit trail."""
    return _approvals_repo.get_all()

def resolve_purchase_request(request_id: int, decision: str) -> bool:
    """
    Approve or reject a pending purchase request ('APPROVED' or 'REJECTED').
    When approved:
    1. Updates request status to 'APPROVED'.
    2. Increments inventory quantity for the item.
    3. Automatically records a new confirmed order in the orders table.
    """
    res = _approvals_repo.resolve(request_id, decision)
    return res.get("status") == "success"

# ----------------- Kitchen Bill of Materials (BOM) & Recipes -----------------

def get_recipes(dish_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve restaurant recipes with ingredients (Bill of Materials)."""
    return _recipes_repo.get_all(dish_name)

def check_dish_feasibility(dish_name: str) -> Dict[str, Any]:
    """
    Calculate how many portions of a dish can be prepared with current inventory stock.
    Identifies the bottleneck (limiting ingredient).
    """
    return _recipes_repo.check_feasibility(dish_name)

def record_dish_sales(dish_name: str, portions: float) -> Dict[str, Any]:
    """
    Deduct inventory ingredients required to prepare/sell specified portions of a dish.
    Validates stock availability and records transaction in kitchen_sales_log.
    """
    return _recipes_repo.record_sales(dish_name, portions)

def get_kitchen_sales_log(limit: int = 15) -> List[Dict[str, Any]]:
    """Retrieve recent kitchen production and dish sales deductions."""
    return _recipes_repo.get_sales_log(limit)
