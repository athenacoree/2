import os
from crewai import LLM

def get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "dummy_key")

    return LLM(
        model=f"openai/{model_name}",
        base_url=base_url,
        api_key=api_key,
        temperature=0.2
    )
