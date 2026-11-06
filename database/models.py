from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False, default="LINE_COOK")  # OWNER, HEAD_CHEF, LINE_COOK
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
        }


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), unique=True, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    category = Column(String(50), nullable=False, default="Pantry")
    min_par_level = Column(Float, default=5.0)
    cost_per_unit = Column(Float, default=0.0)
    expiry_date = Column(String(50), default="")
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        qty = float(self.quantity or 0.0)
        par = float(self.min_par_level or 5.0)
        return {
            "id": self.id,
            "item_name": self.item_name,
            "quantity": qty,
            "unit": self.unit,
            "category": self.category,
            "min_par_level": par,
            "cost_per_unit": float(self.cost_per_unit or 0.0),
            "expiry_date": self.expiry_date or "",
            "is_low_stock": qty <= par,
            "last_updated": self.last_updated.isoformat() if self.last_updated else "",
        }


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    contact_person = Column(String(100), default="")
    phone = Column(String(50), default="")
    email = Column(String(100), default="")
    supplied_categories = Column(String(200), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person or "",
            "phone": self.phone or "",
            "email": self.email or "",
            "supplied_categories": self.supplied_categories or "",
        }


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    supplier_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="PROCESSING")
    order_date = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "item_name": self.item_name,
            "quantity": float(self.quantity or 0.0),
            "unit": self.unit,
            "supplier_name": self.supplier_name,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else "",
        }


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    supplier_name = Column(String(100), nullable=False)
    estimated_cost = Column(Float, default=0.0)
    status = Column(String(30), nullable=False, default="PENDING_APPROVAL")  # PENDING_APPROVAL, APPROVED, REJECTED
    requested_by = Column(String(100), default="HutMate Agent")
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        cost = float(self.estimated_cost or 0.0)
        return {
            "id": self.id,
            "item_name": self.item_name,
            "quantity": float(self.quantity or 0.0),
            "unit": self.unit,
            "supplier_name": self.supplier_name,
            "estimated_cost": cost,
            "estimated_cost_formatted": f"₹{cost:,.2f}" if cost > 0 else "Quote pending",
            "status": self.status,
            "requested_by": self.requested_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
            "resolved_at": self.resolved_at.strftime("%Y-%m-%d %H:%M") if self.resolved_at else "",
        }


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, default="Main Course")
    portion_description = Column(String(100), default="1 portion")
    instructions = Column(Text, default="")

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "dish_name": self.dish_name,
            "category": self.category,
            "portion_description": self.portion_description,
            "instructions": self.instructions,
            "ingredients": [i.to_dict() for i in self.ingredients],
        }


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(100), nullable=False)
    quantity_per_portion = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)

    recipe = relationship("Recipe", back_populates="ingredients")

    def to_dict(self):
        return {
            "ingredient_name": self.ingredient_name,
            "quantity_per_portion": float(self.quantity_per_portion),
            "unit": self.unit,
        }


class KitchenSalesLog(Base):
    __tablename__ = "kitchen_sales_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_name = Column(String(100), nullable=False)
    portions = Column(Float, nullable=False)
    deductions_summary = Column(Text, nullable=False)
    logged_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "dish_name": self.dish_name,
            "portions": float(self.portions),
            "deductions_summary": self.deductions_summary,
            "logged_at": self.logged_at.strftime("%Y-%m-%d %H:%M") if self.logged_at else "",
        }

