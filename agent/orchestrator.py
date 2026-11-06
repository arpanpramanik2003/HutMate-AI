import json
from typing import Dict, Any, List, Optional
from core import config, groq_client
from core.i18n import detect_message_language, LANGUAGES
from rag.retriever import retrieve_relevant_chunks
from agent import tools, schemas
from agent.guardrails import inspect_guardrails
from agent.fallback_agent import run_fallback_agent
from agent.memory import ConversationMemory

memory_manager = ConversationMemory(max_history_turns=8, max_char_budget=12000)

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
            "description": "Add a new item/ingredient directly into the restaurant inventory, or update existing stock levels, unit, category, and par levels.",
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
                    },
                    "min_par_level": {
                        "type": "number",
                        "description": "Minimum threshold before restock alert triggers."
                    },
                    "cost_per_unit": {
                        "type": "number",
                        "description": "Cost per unit in INR (₹)."
                    },
                    "expiry_date": {
                        "type": "string",
                        "description": "Expiration date in YYYY-MM-DD format."
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
   - When reporting sales deductions or low stock alerts, explain clearly in Bengali.
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

    return f"""You are HutMate AI, an intelligent enterprise restaurant operations copilot.
Your job is to assist restaurant owners, head chefs, and kitchen staff with accurate operational metrics, stock monitoring, recipe feasibility, and inventory updates.

Guidelines:
1. Document Knowledge: For hygiene standards, policies, or staff SOPs, use `search_knowledge_base`.
2. Live Data Lookups: For stock levels, use `get_inventory`. For purchase orders, use `get_order_status`. For suppliers, use `get_supplier_details`.
3. Low Stock & Par Level Monitoring: When asked about items running low, shortages, or alerts, use `get_low_stock_alerts`.
4. Kitchen Recipes & BOM (Bill of Materials):
   - To view recipes and ingredients required per portion, use `get_recipes`.
   - When asked how many portions/plates of a dish can be cooked with current stock, use `check_dish_feasibility`. Report the bottleneck ingredient clearly.
   - When staff reports dishes cooked, prepared, or sold (e.g. "We sold 10 plates of Biryani", "15 ta biryani serve kora hoyeche"), use `record_dish_sales` to deduct inventory. If stock is insufficient, notify the user immediately.
5. Proactive Kitchen Recommendations:
   - When ingredients fall below minimum par level thresholds, alert the staff proactively and suggest creating a draft purchase order with the appropriate supplier.
6. Transparency & Safety:
   - Always quote real numbers from tools. Never hallucinate stock or order statuses.
   - Whenever answering from documents, cite the source document name and page.
{lang_instruction}
"""

def execute_tool(name: str, args: Dict[str, Any]) -> Any:
    """Safely validate arguments via Pydantic schemas and execute registered tools."""
    try:
        if name == "get_inventory":
            v = schemas.GetInventoryArgs(**args)
            return tools.get_inventory(v.item_name)
        elif name == "get_low_stock_alerts":
            return tools.get_low_stock_alerts()
        elif name == "get_recipes":
            v = schemas.GetRecipesArgs(**args)
            return tools.get_recipes(v.dish_name)
        elif name == "check_dish_feasibility":
            v = schemas.CheckDishFeasibilityArgs(**args)
            return tools.check_dish_feasibility(v.dish_name)
        elif name == "record_dish_sales":
            v = schemas.RecordDishSalesArgs(**args)
            return tools.record_dish_sales(dish_name=v.dish_name, portions=v.portions)
        elif name == "add_inventory_item":
            v = schemas.AddInventoryItemArgs(**args)
            return tools.upsert_inventory_item(
                item_name=v.item_name,
                quantity=v.quantity,
                unit=v.unit,
                category=v.category,
                min_par_level=v.min_par_level,
                cost_per_unit=v.cost_per_unit,
                expiry_date=v.expiry_date,
            )
        elif name == "delete_inventory_item":
            v = schemas.DeleteInventoryItemArgs(**args)
            return tools.delete_inventory_item(v.item_name)
        elif name == "get_order_status":
            v = schemas.GetOrderStatusArgs(**args)
            return tools.get_order_status(v.order_number)
        elif name == "get_supplier_details":
            v = schemas.GetSupplierDetailsArgs(**args)
            return tools.get_supplier_details(v.supplier_name)
        elif name == "create_purchase_request":
            v = schemas.CreatePurchaseRequestArgs(**args)
            return tools.create_purchase_request(
                item_name=v.item_name,
                quantity=v.quantity,
                unit=v.unit,
                supplier_name=v.supplier_name,
            )
        elif name == "search_knowledge_base":
            v = schemas.SearchKnowledgeBaseArgs(**args)
            return retrieve_relevant_chunks(v.query)
        else:
            return {"error": f"Unknown tool: '{name}'"}
    except Exception as e:
        return {"error": f"Tool argument validation failed for '{name}': {str(e)}"}

def run_agent(user_message: str, conversation_history: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
    """Execute the enterprise agent with guardrails, memory pruning, Groq tool-calling, and fallback."""
    # 1. Dynamic Language Detection
    lang_info = detect_message_language(user_message, default_lang=language)
    effective_lang = lang_info["language"]
    is_explicit_switch = lang_info["is_explicit_switch"]

    # 2. Enterprise Domain Guardrails Check
    is_blocked, deflection_msg = inspect_guardrails(user_message, language=effective_lang)
    if is_blocked:
        return {
            "answer": deflection_msg,
            "tools_used": [],
            "sources": [],
            "detected_language": effective_lang,
            "is_explicit_switch": is_explicit_switch,
            "detected_script": lang_info.get("detected_script"),
            "guardrail_deflected": True,
        }

    # 3. Context Memory Pruning
    pruned_history = memory_manager.prune_history(conversation_history)

    # 4. Attempt LLM Execution via Groq
    try:
        client = groq_client.get_groq_client()
        system_prompt = get_system_prompt(effective_lang, is_explicit_switch=is_explicit_switch)
        messages = [{"role": "system", "content": system_prompt}]
        for m in pruned_history:
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

    except Exception as llm_err:
        # 5. Graceful Cascade to Deterministic Fallback Agent
        fallback_res = run_fallback_agent(user_message, language=effective_lang)
        fallback_res["llm_error"] = str(llm_err)
        fallback_res["is_explicit_switch"] = is_explicit_switch
        fallback_res["detected_script"] = lang_info.get("detected_script")
        return fallback_res
