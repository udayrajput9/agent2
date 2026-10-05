from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm(temperature: float = 0.4, json_mode: bool = False) -> Runnable:
    json_kwargs = {}
    if json_mode:
        json_kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

    groq_llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        **json_kwargs,
    )

    fallbacks = []
    if settings.OPENAI_API_KEY:
        fallbacks.append(
            ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature,
                **json_kwargs,
            )
        )

    # Gemini doesn't take the same response_format kwargs; the json is
    # recovered by extract_json() on the caller side instead.
    fallbacks.append(
        ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )
    )

    return groq_llm.with_fallbacks(fallbacks)
