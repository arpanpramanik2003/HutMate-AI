from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Order

class OrdersRepository:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def _get_session(self) -> Session:
        return self._external_session or SessionLocal()

    def get_all(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            q = db.query(Order)
            if status and status.strip():
                q = q.filter(Order.status == status.strip().upper())
            orders = q.order_by(Order.id.desc()).all()
            return [o.to_dict() for o in orders]

    def get_by_order_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        with self._get_session() as db:
            order = db.query(Order).filter(Order.order_number == order_number.strip().upper()).first()
            return order.to_dict() if order else None

    def upsert(
        self,
        order_number: str,
        item_name: str,
        quantity: float,
        unit: str,
        supplier_name: str,
        status: str = "PROCESSING"
    ) -> Dict[str, Any]:
        with self._get_session() as db:
            num = order_number.strip().upper()
            existing = db.query(Order).filter(Order.order_number == num).first()
            if existing:
                existing.item_name = item_name.strip()
                existing.quantity = float(quantity)
                existing.unit = unit.strip()
                existing.supplier_name = supplier_name.strip()
                existing.status = status.strip().upper()
                order_dict = existing.to_dict()
            else:
                new_ord = Order(
                    order_number=num,
                    item_name=item_name.strip(),
                    quantity=float(quantity),
                    unit=unit.strip(),
                    supplier_name=supplier_name.strip(),
                    status=status.strip().upper()
                )
                db.add(new_ord)
                db.flush()
                order_dict = new_ord.to_dict()
            db.commit()
            return order_dict

    def delete(self, order_id: int) -> int:
        with self._get_session() as db:
            deleted = db.query(Order).filter(Order.id == int(order_id)).delete()
            db.commit()
            return deleted

    def sync_all(self, orders: List[Dict[str, Any]]):
        with self._get_session() as db:
            db.query(Order).delete()
            new_objs = [
                Order(
                    order_number=str(o["order_number"]).strip().upper(),
                    item_name=str(o["item_name"]).strip(),
                    quantity=float(o["quantity"]),
                    unit=str(o["unit"]).strip(),
                    supplier_name=str(o["supplier_name"]).strip(),
                    status=str(o.get("status", "PROCESSING")).strip().upper()
                )
                for o in orders
                if o.get("order_number", "").strip()
            ]
            db.add_all(new_objs)
            db.commit()

