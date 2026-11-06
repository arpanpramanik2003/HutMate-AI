from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.db import SessionLocal
from database.models import Supplier

class SuppliersRepository:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def _get_session(self) -> Session:
        return self._external_session or SessionLocal()

    def get_all(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            q = db.query(Supplier)
            if query and query.strip():
                term = f"%{query.strip()}%"
                q = q.filter(or_(Supplier.name.ilike(term), Supplier.supplied_categories.ilike(term)))
            suppliers = q.all()
            return [s.to_dict() for s in suppliers]

    def upsert(
        self,
        name: str,
        contact_person: str = "",
        phone: str = "",
        email: str = "",
        supplied_categories: str = ""
    ) -> Dict[str, Any]:
        with self._get_session() as db:
            clean_name = name.strip()
            existing = db.query(Supplier).filter(Supplier.name.ilike(clean_name)).first()
            if existing:
                existing.contact_person = contact_person.strip()
                existing.phone = phone.strip()
                existing.email = email.strip()
                existing.supplied_categories = supplied_categories.strip()
                supplier_dict = existing.to_dict()
            else:
                new_sup = Supplier(
                    name=clean_name,
                    contact_person=contact_person.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    supplied_categories=supplied_categories.strip(),
                )
                db.add(new_sup)
                db.flush()
                supplier_dict = new_sup.to_dict()
            db.commit()
            return supplier_dict

    def delete(self, supplier_id: int) -> int:
        with self._get_session() as db:
            deleted = db.query(Supplier).filter(Supplier.id == int(supplier_id)).delete()
            db.commit()
            return deleted

    def sync_all(self, suppliers: List[Dict[str, Any]]):
        with self._get_session() as db:
            db.query(Supplier).delete()
            new_objs = [
                Supplier(
                    name=str(s["name"]).strip(),
                    contact_person=str(s.get("contact_person", "")).strip(),
                    phone=str(s.get("phone", "")).strip(),
                    email=str(s.get("email", "")).strip(),
                    supplied_categories=str(s.get("supplied_categories", "")).strip(),
                )
                for s in suppliers
                if s.get("name", "").strip()
            ]
            db.add_all(new_objs)
            db.commit()

