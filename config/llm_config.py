"""
LLM Configuration - Supports Groq (cloud) and Ollama (local)
Both use open-source models (Llama 3, Mixtral)
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    Returns a LangChain-compatible LLM instance.
    Priority: Groq > Ollama
    """
    groq_key = os.getenv("GROQ_API_KEY")
    ollama_url = os.getenv("OLLAMA_BASE_URL")

    if groq_key and groq_key != "your_groq_api_key_here":
        return _get_groq_llm()
    elif ollama_url:
        return _get_ollama_llm()
    else:
        # Default to Groq with key from env
        return _get_groq_llm()


def _get_groq_llm():
    """Groq - Free API, runs Llama3 / Mixtral at high speed"""
    from langchain_groq import ChatGroq
    model = os.getenv("LLM_MODEL", "llama3-70b-8192")
    print(f"[LLM] Using Groq with model: {model}")
    return ChatGroq(
        model=model,
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


def _get_ollama_llm():
    """Ollama - Fully local, no API key required"""
    from langchain_community.llms import Ollama
    model = os.getenv("OLLAMA_MODEL", "llama3")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"[LLM] Using Ollama at {base_url} with model: {model}")
    return Ollama(model=model, base_url=base_url, temperature=0.3)


def get_crewai_llm():
    """Returns LLM config dict for CrewAI agents"""
    groq_key = os.getenv("GROQ_API_KEY")
    ollama_url = os.getenv("OLLAMA_BASE_URL")

    if groq_key and groq_key != "your_groq_api_key_here":
        model = os.getenv("LLM_MODEL", "llama3-70b-8192")
        return {"model": f"groq/{model}"}
    elif ollama_url:
        model = os.getenv("OLLAMA_MODEL", "llama3")
        return {"model": f"ollama/{model}", "base_url": ollama_url}
    else:
        model = os.getenv("LLM_MODEL", "llama3-70b-8192")
        return {"model": f"groq/{model}"}
