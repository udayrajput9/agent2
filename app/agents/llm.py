from langchain_groq import ChatGroq

from app.config import settings


def get_llm(temperature: float = 0.4, json_mode: bool = False) -> ChatGroq:
    kwargs = {}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        **kwargs,
    )
