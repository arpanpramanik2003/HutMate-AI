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
    assert "min_par_level" in items[0]
    assert "cost_per_unit" in items[0]

def test_low_stock_alerts():
    seed_sample_data()
    alerts = tools.get_low_stock_alerts()
    # In seeded data, Tomatoes (8.5 <= 10.0), Yogurt (6.0 <= 8.0), and Cheese (4.0 <= 10.0) are below par level
    assert len(alerts) >= 2
    item_names = [a["item_name"] for a in alerts]
    assert "Tomatoes" in item_names
    assert "Yogurt" in item_names
    assert alerts[0]["shortfall"] > 0
    assert alerts[0]["estimated_restock_cost"] > 0

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
    # 1. Upsert new item with par level & unit cost
    tools.upsert_inventory_item("Olive Oil", 15.0, "liters", "Pantry", min_par_level=8.0, cost_per_unit=350.0, expiry_date="2027-01-01")
    item = tools.get_inventory("Olive Oil")
    assert len(item) == 1
    assert item[0]["quantity"] == 15.0
    assert item[0]["min_par_level"] == 8.0
    assert item[0]["cost_per_unit"] == 350.0
    item_id = item[0]["id"]

    # 2. Update existing item
    tools.upsert_inventory_item("Olive Oil", 22.5, "liters", "Pantry")
    item_updated = tools.get_inventory("Olive Oil")
    assert item_updated[0]["quantity"] == 22.5

    # 3. Delete item
    tools.delete_inventory_item(item_id)
    assert len(tools.get_inventory("Olive Oil")) == 0

def test_purchase_request_lifecycle_with_cost():
    seed_sample_data()
    # Tomatoes unit cost is 50.0, quantity is 10.0 -> estimated cost should be 500.0
    res = tools.create_purchase_request("Tomatoes", 10.0, "kg", "Fresh Farm Produce")
    req_id = res["id"]
    assert req_id > 0
    assert res["status"] == "PENDING_APPROVAL"
    assert res["estimated_cost"] == 500.0

    # Verify pending
    pending = tools.get_pending_purchase_requests()
    assert any(r["id"] == req_id for r in pending)

    # Approve request
    approved = tools.resolve_purchase_request(req_id, "APPROVED")
    assert approved is True

def test_recipes_and_bill_of_materials():
    seed_sample_data()
    recipes = tools.get_recipes()
    assert len(recipes) >= 3
    biryani = [r for r in recipes if r["dish_name"] == "Dum Chicken Biryani"][0]
    assert len(biryani["ingredients"]) >= 5
    ing_names = [i["ingredient_name"] for i in biryani["ingredients"]]
    assert "Chicken Breast" in ing_names
    assert "Basmati Rice" in ing_names

def test_dish_feasibility_calculation():
    seed_sample_data()
    # In seeded data, Chicken Breast has 14.5 kg. Biryani needs 0.25 kg per portion.
    # 14.5 / 0.25 = 58 portions.
    res = tools.check_dish_feasibility("Dum Chicken Biryani")
    assert res["status"] == "success"
    assert res["max_portions_possible"] > 0
    assert "limiting_ingredient" in res
    assert len(res["ingredients_breakdown"]) >= 5

def test_record_dish_sales_and_stock_deduction():
    seed_sample_data()
    chicken_before = tools.get_inventory("Chicken Breast")[0]["quantity"]
    rice_before = tools.get_inventory("Basmati Rice")[0]["quantity"]

    # Sell 4 portions of Biryani (requires 4 * 0.25 = 1.0 kg chicken, 4 * 0.20 = 0.8 kg rice)
    res = tools.record_dish_sales("Dum Chicken Biryani", 4.0)
    assert res["status"] == "success"
    assert res["portions_prepared"] == 4.0

    chicken_after = tools.get_inventory("Chicken Breast")[0]["quantity"]
    rice_after = tools.get_inventory("Basmati Rice")[0]["quantity"]
    assert chicken_after == round(chicken_before - 1.0, 2)
    assert rice_after == round(rice_before - 0.8, 2)

    # Verify logged in kitchen_sales_log
    logs = tools.get_kitchen_sales_log(1)
    assert len(logs) > 0
    assert logs[0]["dish_name"] == "Dum Chicken Biryani"
    assert logs[0]["portions"] == 4.0

def test_record_dish_sales_insufficient_stock():
    seed_sample_data()
    # Try to cook 1,000 portions of Biryani (stock cannot satisfy)
    res = tools.record_dish_sales("Dum Chicken Biryani", 1000.0)
    assert res["status"] == "insufficient_stock"
    assert len(res["shortages"]) > 0

    # Re-seed back to default
    seed_sample_data()
