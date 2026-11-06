from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import PurchaseRequest, InventoryItem, Order
from core.i18n import normalize_item_name

class ApprovalsRepository:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def _get_session(self) -> Session:
        return self._external_session or SessionLocal()

    def get_all(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            q = db.query(PurchaseRequest)
            if status and status.strip():
                q = q.filter(PurchaseRequest.status == status.strip().upper())
            reqs = q.order_by(PurchaseRequest.id.desc()).all()
            return [r.to_dict() for r in reqs]

    def get_pending(self) -> List[Dict[str, Any]]:
        return self.get_all(status="PENDING_APPROVAL")

    def get_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        with self._get_session() as db:
            req = db.query(PurchaseRequest).filter(PurchaseRequest.id == int(request_id)).first()
            return req.to_dict() if req else None

    def create_draft(
        self,
        item_name: str,
        quantity: float,
        unit: str,
        supplier_name: str,
        estimated_cost: Optional[float] = None,
        requested_by: str = "HutMate Agent"
    ) -> Dict[str, Any]:
        norm = normalize_item_name(item_name)
        resolved_name = norm["canonical"] if norm["matched"] else item_name.strip().title()

        with self._get_session() as db:
            calc_cost = estimated_cost
            if calc_cost is None or float(calc_cost) <= 0.0:
                inv = db.query(InventoryItem).filter(
                    (InventoryItem.item_name == resolved_name) |
                    (InventoryItem.item_name.ilike(f"%{resolved_name}%"))
                ).first()
                unit_cost = float(inv.cost_per_unit or 0.0) if inv else 0.0
                calc_cost = round(float(quantity) * unit_cost, 2)
            else:
                calc_cost = round(float(calc_cost), 2)

            new_req = PurchaseRequest(
                item_name=resolved_name,
                quantity=float(quantity),
                unit=unit.strip(),
                supplier_name=supplier_name.strip(),
                estimated_cost=calc_cost,
                status="PENDING_APPROVAL",
                requested_by=requested_by.strip() or "HutMate Agent"
            )
            db.add(new_req)
            db.commit()
            db.refresh(new_req)

            cost_str = f"₹{calc_cost:,.2f}" if calc_cost > 0 else "Quote pending"
            return {
                "id": new_req.id,
                "item_name": resolved_name,
                "quantity": float(quantity),
                "unit": unit.strip(),
                "supplier_name": supplier_name.strip(),
                "estimated_cost": calc_cost,
                "status": "PENDING_APPROVAL",
                "message": f"Draft purchase request #{new_req.id} created for {quantity} {unit.strip()} of '{resolved_name}' ({cost_str}). Awaiting approval."
            }

    def resolve(self, request_id: int, decision: str, resolved_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve or reject a pending purchase request.
        If APPROVED:
          1. Atomically increments inventory item stock.
          2. Generates confirmed Order record.
          3. Sets status to APPROVED with timestamp.
        """
        dec = decision.strip().upper()
        if dec not in ("APPROVED", "REJECTED"):
            raise ValueError("Decision must be either 'APPROVED' or 'REJECTED'")

        with self._get_session() as db:
            req = db.query(PurchaseRequest).filter(
                PurchaseRequest.id == int(request_id),
                PurchaseRequest.status == "PENDING_APPROVAL"
            ).first()

            if not req:
                return {
                    "status": "error",
                    "message": f"Purchase request #{request_id} not found or already resolved."
                }

            req.status = dec
            req.resolved_at = datetime.now()

            order_record = None
            if dec == "APPROVED":
                # 1. Update/Increment Inventory
                inv = db.query(InventoryItem).filter(InventoryItem.item_name == req.item_name).first()
                if inv:
                    inv.quantity = float(inv.quantity) + float(req.quantity)
                else:
                    inv = InventoryItem(
                        item_name=req.item_name,
                        quantity=float(req.quantity),
                        unit=req.unit,
                        category="Pantry",
                    )
                    db.add(inv)

                # 2. Record Order
                order_num = f"ORD-APR{req.id:04d}"
                existing_ord = db.query(Order).filter(Order.order_number == order_num).first()
                if not existing_ord:
                    order_record = Order(
                        order_number=order_num,
                        item_name=req.item_name,
                        quantity=float(req.quantity),
                        unit=req.unit,
                        supplier_name=req.supplier_name,
                        status="PROCESSING",
                    )
                    db.add(order_record)

            db.commit()
            return {
                "status": "success",
                "request_id": req.id,
                "decision": dec,
                "message": f"Purchase request #{req.id} for '{req.item_name}' was successfully {dec.lower()}."
            }

