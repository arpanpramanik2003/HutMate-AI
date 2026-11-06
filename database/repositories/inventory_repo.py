from typing import Optional, List, Dict, Any
from sqlalchemy import or_
from database.db import SessionLocal
from database.models import InventoryItem
from core.i18n import normalize_item_name

class InventoryRepository:
    def __init__(self, session=None):
        self._external_session = session

    def _get_session(self):
        return self._external_session or SessionLocal()

    def get_all(self, item_name: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            query = db.query(InventoryItem)
            if item_name and item_name.strip():
                norm = normalize_item_name(item_name)
                canonical = norm["canonical"]
                first_word = canonical.split()[0]
                query = query.filter(
                    or_(
                        InventoryItem.item_name.ilike(f"%{item_name.strip()}%"),
                        InventoryItem.item_name.ilike(f"%{canonical}%"),
                        InventoryItem.item_name.ilike(f"%{first_word}%"),
                    )
                )
            items = query.all()
            return [i.to_dict() for i in items]

    def get_low_stock(self) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            items = db.query(InventoryItem).filter(InventoryItem.quantity <= InventoryItem.min_par_level).all()
            alerts = []
            for i in items:
                shortfall = max(0.0, float(i.min_par_level or 5.0) - float(i.quantity or 0.0))
                cost = float(i.cost_per_unit or 0.0)
                alerts.append({
                    "id": i.id,
                    "item_name": i.item_name,
                    "quantity": float(i.quantity),
                    "unit": i.unit,
                    "min_par_level": float(i.min_par_level),
                    "shortfall": round(shortfall, 2),
                    "cost_per_unit": cost,
                    "estimated_restock_cost": round(shortfall * cost, 2),
                    "expiry_date": i.expiry_date or "",
                    "message": f"CRITICAL: '{i.item_name}' is at {i.quantity} {i.unit} (Par: {i.min_par_level} {i.unit}). Shortfall: {round(shortfall, 2)} {i.unit}."
                })
            return alerts

    def upsert(
        self,
        item_name: str,
        quantity: float,
        unit: str,
        category: Optional[str] = None,
        min_par_level: Optional[float] = None,
        cost_per_unit: Optional[float] = None,
        expiry_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        norm = normalize_item_name(item_name)
        resolved_name = norm["canonical"] if norm["matched"] else item_name.strip().title()
        resolved_cat = (category.strip() if category and category.strip() != "None" else norm["category"]) or "Pantry"
        resolved_unit = unit.strip() if unit and unit.strip() != "None" else norm["default_unit"]
        resolved_par = float(min_par_level) if min_par_level is not None else 5.0
        resolved_cost = float(cost_per_unit) if cost_per_unit is not None else 0.0
        resolved_expiry = expiry_date.strip() if expiry_date else ""

        with self._get_session() as db:
            existing = db.query(InventoryItem).filter(InventoryItem.item_name == resolved_name).first()
            if existing:
                existing.quantity = float(quantity)
                existing.unit = resolved_unit
                existing.category = resolved_cat
                if min_par_level is not None and float(min_par_level) > 0:
                    existing.min_par_level = resolved_par
                if cost_per_unit is not None and float(cost_per_unit) > 0:
                    existing.cost_per_unit = resolved_cost
                if resolved_expiry:
                    existing.expiry_date = resolved_expiry
                item_dict = existing.to_dict()
            else:
                new_item = InventoryItem(
                    item_name=resolved_name,
                    quantity=float(quantity),
                    unit=resolved_unit,
                    category=resolved_cat,
                    min_par_level=resolved_par,
                    cost_per_unit=resolved_cost,
                    expiry_date=resolved_expiry,
                )
                db.add(new_item)
                db.flush()
                item_dict = new_item.to_dict()
            db.commit()

        return {
            "status": "success",
            "item": item_dict,
            "item_name": resolved_name,
            "quantity": float(quantity),
            "unit": resolved_unit,
            "category": resolved_cat,
            "min_par_level": resolved_par,
            "cost_per_unit": resolved_cost,
            "expiry_date": resolved_expiry,
            "display_bn": norm.get("display_bn", resolved_name),
            "display_hi": norm.get("display_hi", resolved_name),
            "message": f"Successfully added/updated {quantity} {resolved_unit} of '{resolved_name}' in inventory."
        }

    def delete(self, identifier: Any) -> int:
        with self._get_session() as db:
            if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
                deleted = db.query(InventoryItem).filter(InventoryItem.id == int(identifier)).delete()
            else:
                deleted = db.query(InventoryItem).filter(InventoryItem.item_name.ilike(f"%{str(identifier).strip()}%")).delete()
            db.commit()
            return deleted

    def sync_all(self, items: List[Dict[str, Any]]):
        with self._get_session() as db:
            db.query(InventoryItem).delete()
            new_objects = [
                InventoryItem(
                    item_name=i["item_name"].strip(),
                    quantity=float(i["quantity"]),
                    unit=i["unit"].strip(),
                    category=(i.get("category") or "Pantry").strip(),
                    min_par_level=float(i.get("min_par_level", 5.0) or 5.0),
                    cost_per_unit=float(i.get("cost_per_unit", 0.0) or 0.0),
                    expiry_date=(i.get("expiry_date") or "").strip(),
                )
                for i in items
                if i.get("item_name", "").strip()
            ]
            db.add_all(new_objects)
            db.commit()

