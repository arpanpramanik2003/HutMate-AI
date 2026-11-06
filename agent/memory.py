from typing import List, Dict, Any, Optional
import re

class ConversationMemory:
    """
    Sliding window conversation memory manager.
    Maintains recency, tracks referenced entities, and bounds token context.
    """
    def __init__(self, max_history_turns: int = 8, max_char_budget: int = 12000):
        self.max_history_turns = max_history_turns
        self.max_char_budget = max_char_budget

    def prune_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Prune and validate conversation history to fit within context budget.
        Keeps only valid user and assistant messages, truncating older messages if budget exceeded.
        """
        valid_messages = []
        for m in history:
            role = m.get("role", "")
            content = m.get("content", "")
            if role in ("user", "assistant") and content and content.strip():
                valid_messages.append({"role": role, "content": content.strip()})

        # Apply turn window limit
        trimmed = valid_messages[-self.max_history_turns:]

        # Apply character length budget
        total_chars = sum(len(m["content"]) for m in trimmed)
        while total_chars > self.max_char_budget and len(trimmed) > 2:
            trimmed.pop(0)
            total_chars = sum(len(m["content"]) for m in trimmed)

        return trimmed

    def extract_active_entities(self, history: List[Dict[str, str]]) -> Dict[str, Optional[str]]:
        """
        Inspect recent messages to detect active conversational context
        (such as active dish or ingredient being discussed).
        """
        active_dish = None
        active_ingredient = None

        known_dishes = ["Dum Chicken Biryani", "Paneer Butter Masala", "Garlic Butter Naan"]
        known_ingredients = ["Chicken", "Rice", "Cheese", "Tomatoes", "Butter", "Flour", "Onions", "Yogurt", "Garlic"]

        for m in reversed(history[-4:]):
            content = m.get("content", "")
            if not active_dish:
                for d in known_dishes:
                    if d.lower() in content.lower():
                        active_dish = d
                        break

            if not active_ingredient:
                for ing in known_ingredients:
                    if ing.lower() in content.lower():
                        active_ingredient = ing
                        break

            if active_dish and active_ingredient:
                break

        return {
            "active_dish": active_dish,
            "active_ingredient": active_ingredient,
        }

