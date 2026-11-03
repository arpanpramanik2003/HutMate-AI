import pytest
import pandas as pd
from database.sample_data import seed_sample_data
from agent import tools

def setup_module():
    seed_sample_data()

def test_inventory_lookup():
    items = tools.get_inventory("Chicken")
    assert len(items) > 0
    assert "Chicken Breast" in items[0]["item_name"]
    assert items[0]["quantity"] > 0

def test_order_lookup():
    order = tools.get_order_status("ORD-1001")
    assert order is not None
    assert order["order_number"] == "ORD-1001"
    assert order["item_name"] == "Basmati Rice"

def test_supplier_lookup():
    suppliers = tools.get_supplier_details("ABC Foods")
    assert len(suppliers) > 0
    assert "ABC Foods" in suppliers[0]["name"]

def test_inventory_modification():
    # 1. Upsert new item
    tools.upsert_inventory_item("Olive Oil", 15.0, "liters", "Pantry")
    item = tools.get_inventory("Olive Oil")
    assert len(item) == 1
    assert item[0]["quantity"] == 15.0
    item_id = item[0]["id"]

    # 2. Update existing item
    tools.upsert_inventory_item("Olive Oil", 22.5, "liters", "Pantry")
    item_updated = tools.get_inventory("Olive Oil")
    assert item_updated[0]["quantity"] == 22.5

    # 3. Delete item
    tools.delete_inventory_item(item_id)
    assert len(tools.get_inventory("Olive Oil")) == 0

def test_sync_from_dataframe():
    test_df = pd.DataFrame([
        {"item_name": "Test Spice", "quantity": 5.0, "unit": "kg", "category": "Spices"},
        {"item_name": "Test Milk", "quantity": 10.0, "unit": "liters", "category": "Dairy"}
    ])
    tools.sync_inventory_from_dataframe(test_df)
    items = tools.get_inventory()
    assert len(items) == 2
    assert any(i["item_name"] == "Test Spice" for i in items)

    # Re-seed back to default
    seed_sample_data()

def test_purchase_request_lifecycle():
    # 1. Create draft request
    res = tools.create_purchase_request("Tomatoes", 10.0, "kg", "Fresh Farm Produce")
    req_id = res["id"]
    assert req_id > 0
    assert res["status"] == "PENDING_APPROVAL"

    # 2. Check pending list
    pending = tools.get_pending_purchase_requests()
    assert any(r["id"] == req_id for r in pending)

    # 3. Approve request
    approved = tools.resolve_purchase_request(req_id, "APPROVED")
    assert approved is True

    # 4. Verify no longer pending
    pending_after = tools.get_pending_purchase_requests()
    assert not any(r["id"] == req_id for r in pending_after)
