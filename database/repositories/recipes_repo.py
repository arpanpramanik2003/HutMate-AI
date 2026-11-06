from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Recipe, RecipeIngredient, InventoryItem, KitchenSalesLog
from core.i18n import normalize_item_name

class RecipesRepository:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def _get_session(self) -> Session:
        return self._external_session or SessionLocal()

    def get_all(self, dish_name: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            query = db.query(Recipe)
            if dish_name and dish_name.strip():
                query = query.filter(Recipe.dish_name.ilike(f"%{dish_name.strip()}%"))
            recipes = query.all()
            return [r.to_dict() for r in recipes]

    def get_by_name(self, dish_name: str) -> Optional[Dict[str, Any]]:
        with self._get_session() as db:
            recipe = db.query(Recipe).filter(Recipe.dish_name.ilike(f"%{dish_name.strip()}%")).first()
            return recipe.to_dict() if recipe else None

    def check_feasibility(self, dish_name: str) -> Dict[str, Any]:
        """
        Calculate how many portions of a dish can be prepared with current inventory stock.
        Identifies the bottleneck (limiting ingredient).
        """
        with self._get_session() as db:
            recipe = db.query(Recipe).filter(Recipe.dish_name.ilike(f"%{dish_name.strip()}%")).first()
            if not recipe:
                return {
                    "status": "error",
                    "message": f"Recipe for '{dish_name}' not found in master cookbook."
                }

            if not recipe.ingredients:
                return {
                    "status": "error",
                    "message": f"No ingredients configured for '{recipe.dish_name}'."
                }

            feasibility_breakdown = []
            max_portions = float("inf")
            limiting_ingredient = None

            for ing in recipe.ingredients:
                ing_name = ing.ingredient_name
                norm = normalize_item_name(ing_name)
                canonical = norm["canonical"]

                # Find inventory item
                inv = db.query(InventoryItem).filter(
                    (InventoryItem.item_name == canonical) |
                    (InventoryItem.item_name.ilike(f"%{ing_name}%")) |
                    (InventoryItem.item_name.ilike(f"%{canonical}%"))
                ).first()

                current_stock = float(inv.quantity) if inv else 0.0
                needed_per_portion = float(ing.quantity_per_portion)

                if needed_per_portion > 0:
                    portions_from_this = current_stock / needed_per_portion
                else:
                    portions_from_this = float("inf")

                if portions_from_this < max_portions:
                    max_portions = portions_from_this
                    limiting_ingredient = ing_name

                feasibility_breakdown.append({
                    "ingredient": ing_name,
                    "ingredient_name": ing_name,
                    "needed_per_portion": needed_per_portion,
                    "unit": ing.unit,
                    "current_stock": current_stock,
                    "possible_portions": round(portions_from_this, 1) if portions_from_this != float("inf") else 9999.0,
                    "max_portions_possible": int(portions_from_this) if portions_from_this != float("inf") else 9999,
                })

            final_portions = int(max_portions) if max_portions != float("inf") else 0

            return {
                "status": "success",
                "dish_name": recipe.dish_name,
                "category": recipe.category,
                "portion_description": recipe.portion_description,
                "max_portions": final_portions,
                "max_portions_possible": final_portions,
                "limiting_ingredient": limiting_ingredient if final_portions < 9999 else "None (Ample stock)",
                "breakdown": feasibility_breakdown,
                "ingredients_breakdown": feasibility_breakdown,
                "message": f"You can currently prepare {final_portions} portion(s) of '{recipe.dish_name}'. Bottleneck ingredient: {limiting_ingredient or 'None'}."
            }

    def record_sales(self, dish_name: str, portions: float) -> Dict[str, Any]:
        """
        Record kitchen sales or food preparation, atomically deducting required ingredients from stock.
        """
        if portions <= 0:
            return {"status": "error", "message": "Portions must be greater than zero."}

        with self._get_session() as db:
            recipe = db.query(Recipe).filter(Recipe.dish_name.ilike(f"%{dish_name.strip()}%")).first()
            if not recipe:
                return {"status": "error", "message": f"Recipe for '{dish_name}' not found."}

            # 1. Pre-flight stock availability check
            shortages = []
            deduction_plan = []
            for ing in recipe.ingredients:
                ing_name = ing.ingredient_name
                norm = normalize_item_name(ing_name)
                canonical = norm["canonical"]

                inv = db.query(InventoryItem).filter(
                    (InventoryItem.item_name == canonical) |
                    (InventoryItem.item_name.ilike(f"%{ing_name}%")) |
                    (InventoryItem.item_name.ilike(f"%{canonical}%"))
                ).first()

                needed_total = float(ing.quantity_per_portion) * float(portions)
                available = float(inv.quantity) if inv else 0.0

                if available < needed_total:
                    shortages.append(
                        f"'{ing_name}' (need {needed_total:.2f} {ing.unit}, have {available:.2f} {ing.unit})"
                    )
                deduction_plan.append((inv, ing_name, needed_total, ing.unit))

            if shortages:
                return {
                    "status": "insufficient_stock",
                    "dish_name": recipe.dish_name,
                    "requested_portions": portions,
                    "shortages": shortages,
                    "message": f"Cannot fulfill {portions} portions of '{recipe.dish_name}'. Insufficient stock for: {', '.join(shortages)}."
                }

            # 2. Execute atomic stock deduction
            deduction_strings = []
            post_alerts = []
            for inv_item, name, needed, unit in deduction_plan:
                if inv_item:
                    inv_item.quantity = max(0.0, float(inv_item.quantity) - needed)
                    if inv_item.quantity <= inv_item.min_par_level:
                        post_alerts.append(
                            f"CRITICAL: '{inv_item.item_name}' is at {inv_item.quantity:.2f} {inv_item.unit} (Par: {inv_item.min_par_level} {inv_item.unit})."
                        )
                deduction_strings.append(f"{needed:.2f} {unit} {name}")

            summary_text = f"Prepared {portions}x {recipe.dish_name} (Deducted: {', '.join(deduction_strings)})"
            log_entry = KitchenSalesLog(
                dish_name=recipe.dish_name,
                portions=float(portions),
                deductions_summary=summary_text
            )
            db.add(log_entry)
            db.commit()

            return {
                "status": "success",
                "dish_name": recipe.dish_name,
                "portions_prepared": float(portions),
                "deductions": deduction_strings,
                "low_stock_warnings": post_alerts,
                "message": f"Successfully deducted ingredients for {portions}x '{recipe.dish_name}'. Inventory updated."
            }

    def get_sales_log(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_session() as db:
            logs = db.query(KitchenSalesLog).order_by(KitchenSalesLog.id.desc()).limit(limit).all()
            return [l.to_dict() for l in logs]
