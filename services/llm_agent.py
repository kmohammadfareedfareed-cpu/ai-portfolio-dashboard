"""
llm_agent.py
Grounded natural-language query panel, plus a structured per-ticker AI
recommendation (action + justification), in the spirit of the
AI-Stock-Analysis-Dashboard repo's analysis flow. The LLM only ever sees
metrics this app has already computed -- it explains and reasons over real
numbers instead of guessing, and never invents price data.
Supports Anthropic, OpenAI, or OpenRouter (any model) depending on LLM_PROVIDER.
"""
import json

from config import (
    LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY,
    OPENROUTER_API_KEY, OPENROUTER_MODEL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
)

SYSTEM_PROMPT = (
    "You are a financial analysis assistant embedded in a stock dashboard. "
    "Answer the user's question using ONLY the computed metrics and data context provided below. "
    "Be concise and specific, and reference the actual numbers in the context. "
    "If the context doesn't contain enough information to answer, say so clearly instead of guessing. "
    "Frame observations as informational commentary, not personalized investment advice."
)

RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a financial analysis assistant. Given computed technical metrics for a stock, "
    "respond with ONLY a JSON object (no markdown fences, no extra text) with exactly two keys: "
    '"action" (one of "Bullish", "Bearish", or "Neutral") and "justification" '
    "(2-3 sentences explaining the call, referencing the actual metric values given). "
    "Base the call strictly on the provided metrics. This is informational commentary, not financial advice."
)


def _build_context(ticker: str, metrics: dict) -> str:
    return f"Ticker: {ticker}\nComputed metrics and data:\n{json.dumps(metrics, indent=2, default=str)}"


def ask_llm(question: str, ticker: str, metrics: dict) -> str:
    """Free-form grounded Q&A."""
    context = _build_context(ticker, metrics)
    user_content = f"{context}\n\nQuestion: {question}"
    return _dispatch(SYSTEM_PROMPT, user_content)


def get_ticker_recommendation(ticker: str, metrics: dict) -> dict:
    """
    Structured call: returns {"action": "Bullish"|"Bearish"|"Neutral", "justification": "..."}.
    Falls back to a Neutral/explanatory stub if the LLM call fails or returns unparseable JSON,
    so the UI never crashes on a bad response.
    """
    context = _build_context(ticker, metrics)
    raw = _dispatch(RECOMMENDATION_SYSTEM_PROMPT, context)
    cleaned = raw.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        parsed = json.loads(cleaned)
        action = parsed.get("action", "Neutral")
        justification = parsed.get("justification", raw)
        if action not in {"Bullish", "Bearish", "Neutral"}:
            action = "Neutral"
        return {"action": action, "justification": justification}
    except (json.JSONDecodeError, AttributeError):
        return {"action": "Neutral", "justification": raw or "The model did not return a parseable response."}


def _dispatch(system_prompt: str, user_content: str) -> str:
    if LLM_PROVIDER == "anthropic":
        return _ask_anthropic(system_prompt, user_content)
    elif LLM_PROVIDER == "openai":
        return _ask_openai(system_prompt, user_content)
    elif LLM_PROVIDER == "openrouter":
        return _ask_openrouter(system_prompt, user_content)
    elif LLM_PROVIDER == "google":
        return _ask_google(system_prompt, user_content)
    return "No LLM provider configured. Set LLM_PROVIDER to 'anthropic', 'openai', 'openrouter', or 'google' in your .env file."


def _ask_anthropic(system_prompt: str, user_content: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "Missing ANTHROPIC_API_KEY. Add it to your .env file."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
    except Exception as e:
        return f"LLM request failed: {e}"


def _ask_openai(system_prompt: str, user_content: str) -> str:
    if not OPENAI_API_KEY:
        return "Missing OPENAI_API_KEY. Add it to your .env file."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=600,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM request failed: {e}"


def _ask_openrouter(system_prompt: str, user_content: str) -> str:
    """
    OpenRouter exposes an OpenAI-compatible API, so we reuse the `openai` SDK
    with a different base_url -- this pattern (and the free deepseek default
    model) mirrors the AI-Stock-Analysis-Dashboard repo's approach, letting
    you run this without a paid API key.
    """
    if not OPENROUTER_API_KEY:
        return "Missing OPENROUTER_API_KEY. Add it to your .env file (OpenRouter has free-tier models)."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=600,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM request failed: {e}"


def _ask_google(system_prompt: str, user_content: str) -> str:
    """
    Uses Google's current unified Gen AI SDK (`google-genai`, imported as
    `from google import genai`). Note: the older `google.generativeai`
    package is deprecated -- if you see import errors, make sure you've
    installed `google-genai`, not `google-generativeai`.
    """
    if not GOOGLE_API_KEY:
        return "Missing GOOGLE_API_KEY. Add it to your .env file."
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=GOOGLE_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=600,
            ),
        )
        return response.text
    except Exception as e:
        return f"LLM request failed: {e}"
