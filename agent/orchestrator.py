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
                        "description": "Name of the ingredient or item (e.g. 'Cheese', 'Olive Oil', 'Tomatoes'). If user said 'add this', use the item from conversation context."
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Quantity to add to inventory."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement (e.g. 'packets', 'kg', 'liters', 'units', 'grams', 'cans', 'boxes'). Defaults to the unit mentioned or 'units'."
                    },
                    "category": {
                        "type": "string",
                        "description": "Food or pantry category. Choose from: 'Dairy', 'Produce', 'Poultry', 'Meat', 'Grains', 'Spices', 'Pantry', 'Beverages'. If user did not specify, intelligently infer the appropriate category (e.g. Cheese -> 'Dairy', Tomatoes -> 'Produce', Rice -> 'Grains', Oil -> 'Pantry')."
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
   - If the user explicitly instructed to speak in Bengali (e.g. 'speak in Bengali', 'বাংলায় বলো'), warmly acknowledge the switch in Bengali (e.g., 'অবশ্যই! এখন থেকে আমি আপনার সাথে বাংলায় কথা বলছি।').
   - When mentioning ingredients, state both or the Bengali term (e.g., Potatoes -> 'আলু (Potatoes)', Cheese -> 'পনির / চিজ (Cheese)', Chicken Breast -> 'মুরগির মাংস (Chicken)').
   - For spelling mistakes (e.g. 'potto', 'alu', 'chiken', 'tamatar'), smartly recognize the intent, execute the tool, and answer in Bengali.
   - Tool arguments (like item_name) should be in canonical English (e.g. item_name='Potatoes', item_name='Cheese').
"""
    elif language == "hi":
        lang_instruction = """
7. CONVERSATIONAL LANGUAGE REQUIREMENT: HINDI (हिंदी)
   - The user is communicating in Hindi (हिंदी) or has explicitly requested to converse in Hindi.
   - You MUST formulate your answers, operational confirmations, and explanations in fluent, polite Hindi (हिंदी).
   - If the user explicitly instructed to speak in Hindi, warmly acknowledge the switch in Hindi (e.g., 'ज़रूर! अब से मैं आपसे हिंदी में बातचीत करूँगा।').
   - When mentioning ingredients, provide Hindi terms (e.g., Potatoes -> 'आलू (Potatoes)', Cheese -> 'पनीर (Cheese)').
   - Tool arguments (like item_name) should be in canonical English.
"""
    else:
        lang_instruction = """
7. CONVERSATIONAL LANGUAGE REQUIREMENT: ENGLISH
   - The user is communicating in English or has requested to converse in English.
   - Formulate your answers in clear, professional English.
   - If the user asked to switch language (e.g. 'talk in English' or 'switch to English'), warmly acknowledge the change in English.
   - If users ask for Bengali/Hindi meanings (e.g. 'what is potato in bengali?'), provide them accurately (e.g. 'আলু').
"""

    return f"""You are HutMate AI, an intelligent restaurant operations copilot.
Your job is to assist restaurant owners, managers, and kitchen staff with accurate, operational information and proactive tasks.

Guidelines:
1. Document Knowledge: For recipes, menus, food hygiene, or staff SOPs, use `search_knowledge_base`.
2. Live Data Lookups: For current inventory quantities, order statuses, or supplier contacts, use `get_inventory`, `get_order_status`, `get_supplier_details`.
3. Inventory Modifications: When the user asks to add an item to the inventory (e.g. "add 5 packets of cheese", "add this in the inventory for 5 packets and add sufficient category", "5 packet alu add koro", "পনির যোগ করুন"):
   - Smart Typo & Multilingual Resolution: Understand typos and foreign/phonetic words (e.g., 'potto', 'patato', 'alu', 'aaloo' -> 'Potatoes'; 'cheez', 'paneer' -> 'Cheese'; 'chikn', 'murgi' -> 'Chicken Breast').
   - Context Resolution: If the user refers to an item discussed in previous messages (e.g., "do you have cheese?" followed by "then add this in the inventory for 5 packets"), recognize that "this" refers to "Cheese".
   - Category Inference: If not specified by user, automatically infer the correct category:
     * Cheese, Milk, Yogurt, Butter -> 'Dairy'
     * Potatoes, Onions, Tomatoes, Herbs -> 'Produce'
     * Chicken, Turkey -> 'Poultry'
     * Rice, Wheat, Flour -> 'Grains'
     * Oil, Ghee, Vinegar, Cans -> 'Pantry'
   - Always invoke `add_inventory_item`. NEVER say "I don't have a way to edit live inventory directly".
4. Action Proposals: When asked to prepare, draft, or order items through suppliers, use `create_purchase_request`. Make sure to confirm that the request is drafted and pending manager approval.
5. Transparency: Whenever answering from documents, cite the source document name and page. If evidence is not found, state it clearly.
6. Safety: Never guess live inventory counts or order statuses; always consult the tools.
{lang_instruction}
"""

def execute_tool(name: str, args: Dict[str, Any]) -> Any:
    """Safely execute a registered tool function."""
    if name == "get_inventory":
        return tools.get_inventory(args.get("item_name"))
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
    """
    Execute the agent tool-calling loop:
    1. Detect conversational language or in-chat language change intent dynamically.
    2. Format prompt with dynamic multilingual system prompt matching user language.
    3. If Groq requests tools, execute them safely in Python.
    4. Return final answer, tool activity, citations, and detected language metadata.
    """
    # Dynamic Language Detection from user prompt & context
    lang_info = detect_message_language(user_message, default_lang=language)
    effective_lang = lang_info["language"]
    is_explicit_switch = lang_info["is_explicit_switch"]

    client = groq_client.get_groq_client()
    
    # Format messages with dynamic multilingual system prompt
    system_prompt = get_system_prompt(effective_lang, is_explicit_switch=is_explicit_switch)
    messages = [{"role": "system", "content": system_prompt}]
    # Append recent conversation history (max 8 messages)
    for m in conversation_history[-8:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    tool_activities = []
    sources = []

    # Bounded iteration loop (max 4 turns)
    for _ in range(4):
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            tools=ALLOWED_TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )

        response_message = response.choices[0].message

        # If no tool called, return the final response
        if not response_message.tool_calls:
            return {
                "answer": response_message.content or "No response generated.",
                "tools_used": tool_activities,
                "sources": sources,
                "detected_language": effective_lang,
                "is_explicit_switch": is_explicit_switch,
                "detected_script": lang_info.get("detected_script")
            }

        # Otherwise, process tool calls
        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except Exception:
                fn_args = {}

            tool_result = execute_tool(fn_name, fn_args)
            tool_activities.append({"tool": fn_name, "args": fn_args, "result": tool_result})

            # If search_knowledge_base was invoked, extract sources
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

