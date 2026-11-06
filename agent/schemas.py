from typing import Optional
from pydantic import BaseModel, Field, field_validator

class GetInventoryArgs(BaseModel):
    item_name: Optional[str] = Field(default=None, description="Name or keyword of item.")

    @field_validator("item_name", mode="before")
    @classmethod
    def clean_name(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class GetLowStockAlertsArgs(BaseModel):
    pass


class GetRecipesArgs(BaseModel):
    dish_name: Optional[str] = Field(default=None, description="Dish name or keyword.")

    @field_validator("dish_name", mode="before")
    @classmethod
    def clean_dish(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class CheckDishFeasibilityArgs(BaseModel):
    dish_name: str = Field(..., description="Name of the dish to check feasibility for.")

    @field_validator("dish_name")
    @classmethod
    def clean_dish(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("Dish name cannot be empty.")
        return s


class RecordDishSalesArgs(BaseModel):
    dish_name: str = Field(..., description="Name of the dish cooked/sold.")
    portions: float = Field(default=1.0, description="Portions cooked or sold.")

    @field_validator("dish_name")
    @classmethod
    def clean_dish(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("Dish name cannot be empty.")
        return s

    @field_validator("portions", mode="before")
    @classmethod
    def parse_portions(cls, v):
        try:
            val = float(v)
            if val <= 0:
                raise ValueError("Portions must be greater than zero.")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Invalid portions number: {v}")


class AddInventoryItemArgs(BaseModel):
    item_name: str = Field(..., description="Item or ingredient name.")
    quantity: float = Field(..., description="Quantity of the item.")
    unit: str = Field(default="kg", description="Unit of measurement.")
    category: Optional[str] = Field(default="Pantry", description="Food category.")
    min_par_level: Optional[float] = Field(default=5.0, description="Minimum par level threshold.")
    cost_per_unit: Optional[float] = Field(default=0.0, description="Unit cost in INR.")
    expiry_date: Optional[str] = Field(default="", description="Expiration date.")

    @field_validator("quantity", "min_par_level", "cost_per_unit", mode="before")
    @classmethod
    def parse_floats(cls, v):
        if v is None or v == "":
            return 0.0
        return float(v)


class DeleteInventoryItemArgs(BaseModel):
    item_name: str = Field(..., description="Name of item to delete.")

    @field_validator("item_name")
    @classmethod
    def clean_name(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("Item name cannot be empty.")
        return s


class GetOrderStatusArgs(BaseModel):
    order_number: str = Field(..., description="Order code.")

    @field_validator("order_number")
    @classmethod
    def clean_order(cls, v):
        s = str(v).strip().upper()
        if not s:
            raise ValueError("Order number cannot be empty.")
        return s


class GetSupplierDetailsArgs(BaseModel):
    supplier_name: Optional[str] = Field(default=None, description="Supplier name or keyword.")


class CreatePurchaseRequestArgs(BaseModel):
    item_name: str = Field(..., description="Item to purchase.")
    quantity: float = Field(..., description="Quantity to purchase.")
    unit: str = Field(default="kg", description="Unit of measurement.")
    supplier_name: str = Field(..., description="Supplier to purchase from.")

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_qty(cls, v):
        val = float(v)
        if val <= 0:
            raise ValueError("Purchase quantity must be greater than zero.")
        return val


class SearchKnowledgeBaseArgs(BaseModel):
    query: str = Field(..., description="Search query string.")

    @field_validator("query")
    @classmethod
    def clean_query(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("Query string cannot be empty.")
        return s

