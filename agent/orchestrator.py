import json
from typing import Dict, Any, List, Optional
from core import config, groq_client
from core.i18n import detect_message_language, LANGUAGES
from rag.retriever import retrieve_relevant_chunks
from agent import tools

# Allowed tool schemas for Groq / OpenAI-compatible tool calling
ALLOWED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": "Check current restaurant inventory and stock levels for ingredients or items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name or keyword of the item (e.g., 'Chicken', 'Rice'). Leave empty to list all."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_alerts",
            "description": "Check which inventory items are below their minimum par level thresholds and need restocking.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Lookup live status, quantity, and supplier for a restaurant purchase order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number code, such as 'ORD-1001'."
                    }
                },
                "required": ["order_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supplier_details",
            "description": "Lookup supplier directory, contact info, and supplied food categories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_name": {
                        "type": "string",
                        "description": "Supplier name or category keyword (e.g. 'ABC Foods', 'Poultry')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_inventory_item",
            "description": "Add a new item/ingredient directly into the restaurant inventory, or update existing stock levels, unit, and category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name of the ingredient or item (e.g. 'Cheese', 'Olive Oil', 'Tomatoes')."
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Quantity to add to inventory."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement (e.g. 'packets', 'kg', 'liters', 'units', 'grams')."
                    },
                    "category": {
                        "type": "string",
                        "description": "Food category: 'Dairy', 'Produce', 'Poultry', 'Meat', 'Grains', 'Spices', 'Pantry', 'Beverages'."
                    }
                },
                "required": ["item_name", "quantity", "unit", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_inventory_item",
            "description": "Remove an ingredient or item from the live inventory by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name or keyword of the item to delete from inventory."
                    }
                },
                "required": ["item_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_purchase_request",
            "description": "Draft a purchase request for an ingredient that requires manager approval before execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Ingredient or item name to purchase."},
                    "quantity": {"type": "number", "description": "Quantity to purchase."},
                    "unit": {"type": "string", "description": "Unit of measurement (e.g., 'kg', 'liters')."},
                    "supplier_name": {"type": "string", "description": "Supplier name to order from."}
                },
                "required": ["item_name", "quantity", "unit", "supplier_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipes",
            "description": "Lookup recipe details, preparation methods, and ingredient Bill of Materials (BOM) for menu dishes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {
                        "type": "string",
                        "description": "Dish name (e.g. 'Biryani', 'Paneer Butter Masala', 'Naan'). Leave empty to list all."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_dish_feasibility",
            "description": "Calculate how many portions of a dish can be prepared based on current inventory stock, and identify the limiting bottleneck ingredient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {
                        "type": "string",
                        "description": "Dish name to check (e.g. 'Dum Chicken Biryani', 'Paneer Butter Masala')."
                    }
                },
                "required": ["dish_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_dish_sales",
            "description": "Deduct raw ingredients from live inventory when dishes are prepared or sold in the restaurant kitchen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {
                        "type": "string",
                        "description": "Name of the dish prepared or sold (e.g. 'Dum Chicken Biryani', 'Paneer Butter Masala')."
                    },
                    "portions": {
                        "type": "number",
                        "description": "Number of portions or plates prepared/sold."
                    }
                },
                "required": ["dish_name", "portions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search restaurant policy documents, SOPs, menus, and food safety standards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'food storage temperature', 'biryani ingredients')."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def get_system_prompt(language: str = "en", is_explicit_switch: bool = False) -> str:
    lang_instruction = ""
    if language == "bn":
        lang_instruction = """
7. CONVERSATIONAL LANGUAGE REQUIREMENT: BENGALI (বাংলা)
   - The user is communicating in Bengali (বাংলা) or has explicitly requested to converse in Bengali.
   - You MUST formulate your answers, operational confirmations, and explanations in fluent, natural Bengali (বাংলা).
   - If the user explicitly instructed to speak in Bengali, warmly acknowledge the switch in Bengali (e.g., 'অবশ্যই! এখন থেকে আমি আপনার সাথে বাংলায় কথা বলছি।').
   - When mentioning ingredients or dishes, state both or the Bengali term (e.g., Potatoes -> 'আলু (Potatoes)', Cheese -> 'পনির / চিজ (Cheese)', Chicken Breast -> 'মুরগির মাংস (Chicken)').
   - When reporting sales deductions or low stock alerts, explain clearly in Bengali (e.g., '১০ প্লেট বিরিয়ানির জন্য উপাদান বাদ দেওয়া হয়েছে।').
   - Tool arguments (like item_name, dish_name) should be in canonical English.
"""
    elif language == "hi":
        lang_instruction = """
7. CONVERSATIONAL LANGUAGE REQUIREMENT: HINDI (हिंदी)
   - The user is communicating in Hindi (हिंदी) or has explicitly requested to converse in Hindi.
   - You MUST formulate your answers, operational confirmations, and explanations in fluent, polite Hindi (हिंदी).
   - When mentioning ingredients, provide Hindi terms (e.g., Potatoes -> 'आलू (Potatoes)', Cheese -> 'पनीर (Cheese)').
   - Tool arguments should be in canonical English.
"""
    else:
        lang_instruction = """
7. CONVERSATIONAL LANGUAGE REQUIREMENT: ENGLISH
   - Formulate your answers in clear, professional English.
"""

    return f"""You are HutMate AI, an intelligent restaurant operations copilot.
Your job is to assist restaurant owners, managers, and kitchen staff with accurate operational information, stock monitoring, recipe calculation, and inventory updates.

Guidelines:
1. Document Knowledge: For hygiene standards, policies, or staff SOPs, use `search_knowledge_base`.
2. Live Data Lookups: For stock levels, use `get_inventory`. For purchase orders, use `get_order_status`. For suppliers, use `get_supplier_details`.
3. Low Stock & Par Level Monitoring: When asked about items running low, shortages, or alerts, use `get_low_stock_alerts`.
4. Kitchen Recipes & BOM (Bill of Materials):
   - To view recipes and ingredients required per portion, use `get_recipes`.
   - When asked how many portions/plates of a dish can be cooked with current stock, use `check_dish_feasibility`. Report the bottleneck ingredient clearly.
   - When staff reports dishes cooked, prepared, or sold (e.g. "We sold 10 plates of Biryani", "15 ta biryani serve kora hoyeche"), use `record_dish_sales` to deduct inventory. If stock is insufficient, notify the user immediately.
5. Inventory Modifications:
   - For direct additions (e.g. "add 5 packets of cheese"), infer categories automatically and invoke `add_inventory_item`.
   - When asked to draft/prepare an order with a supplier, use `create_purchase_request` (which calculates estimated costs).
6. Transparency & Safety:
   - Always quote real numbers from tools. Never hallucinate stock or order statuses.
   - Whenever answering from documents, cite the source document name and page.
{lang_instruction}
"""

def execute_tool(name: str, args: Dict[str, Any]) -> Any:
    """Safely execute a registered tool function."""
    if name == "get_inventory":
        return tools.get_inventory(args.get("item_name"))
    elif name == "get_low_stock_alerts":
        return tools.get_low_stock_alerts()
    elif name == "get_recipes":
        return tools.get_recipes(args.get("dish_name"))
    elif name == "check_dish_feasibility":
        return tools.check_dish_feasibility(args.get("dish_name", ""))
    elif name == "record_dish_sales":
        return tools.record_dish_sales(
            dish_name=args.get("dish_name", ""),
            portions=float(args.get("portions", 1.0))
        )
    elif name == "add_inventory_item":
        return tools.upsert_inventory_item(
            item_name=args.get("item_name", "").strip(),
            quantity=float(args.get("quantity", 0)),
            unit=args.get("unit", "units").strip(),
            category=args.get("category", "Pantry").strip()
        )
    elif name == "delete_inventory_item":
        return tools.delete_inventory_item(args.get("item_name", "").strip())
    elif name == "get_order_status":
        return tools.get_order_status(args.get("order_number", ""))
    elif name == "get_supplier_details":
        return tools.get_supplier_details(args.get("supplier_name"))
    elif name == "create_purchase_request":
        return tools.create_purchase_request(
            item_name=args.get("item_name", ""),
            quantity=float(args.get("quantity", 0)),
            unit=args.get("unit", "units"),
            supplier_name=args.get("supplier_name", "")
        )
    elif name == "search_knowledge_base":
        return retrieve_relevant_chunks(args.get("query", ""))
    else:
        return {"error": f"Unknown tool: {name}"}

def run_agent(user_message: str, conversation_history: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
    """Execute the agent tool-calling loop with dynamic language handling."""
    lang_info = detect_message_language(user_message, default_lang=language)
    effective_lang = lang_info["language"]
    is_explicit_switch = lang_info["is_explicit_switch"]

    client = groq_client.get_groq_client()
    
    system_prompt = get_system_prompt(effective_lang, is_explicit_switch=is_explicit_switch)
    messages = [{"role": "system", "content": system_prompt}]
    for m in conversation_history[-8:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    tool_activities = []
    sources = []

    for _ in range(4):
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=ALLOWED_TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )

        response_message = response.choices[0].message

        if not response_message.tool_calls:
            return {
                "answer": response_message.content or "No response generated.",
                "tools_used": tool_activities,
                "sources": sources,
                "detected_language": effective_lang,
                "is_explicit_switch": is_explicit_switch,
                "detected_script": lang_info.get("detected_script")
            }

        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except Exception:
                fn_args = {}

            tool_result = execute_tool(fn_name, fn_args)
            tool_activities.append({"tool": fn_name, "args": fn_args, "result": tool_result})

            if fn_name == "search_knowledge_base" and isinstance(tool_result, list):
                for item in tool_result:
                    if isinstance(item, dict) and "source" in item:
                        sources.append(f"{item['source']} (Page {item.get('page', 1)})")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, default=str),
            })

    return {
        "answer": "Reached maximum tool execution turns.",
        "tools_used": tool_activities,
        "sources": sources,
        "detected_language": effective_lang,
        "is_explicit_switch": is_explicit_switch,
        "detected_script": lang_info.get("detected_script")
    }
