import os
from groq import Groq
from core import config

def get_groq_client() -> Groq:
    """Return an authenticated Groq client."""
    api_key = config.GROQ_API_KEY
    if not api_key or api_key == "placeholder_groq_api_key":
        raise ValueError(
            "GROQ_API_KEY is missing or set to placeholder in your .env file. "
            "Please add a valid Groq API key to .env."
        )
    return Groq(api_key=api_key)

def chat_completion(messages: list[dict], model: str = None, temperature: float = 0.2) -> str:
    """Send conversation messages to Groq model and return the generated answer."""
    client = get_groq_client()
    selected_model = model or config.GROQ_MODEL
    
    response = client.chat.completions.create(
        model=selected_model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

