import httpx

from . import config


class LLMError(Exception):
    """Raised when the LLM call fails. The message is safe to show to users."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def ask_llm(prompt: str, system: str | None = None) -> str:
    if not config.OPENROUTER_API_KEY or not config.OPENROUTER_MODEL:
        raise LLMError("Server is missing OPENROUTER_API_KEY or OPENROUTER_MODEL", 500)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    # payload = {"model": config.OPENROUTER_MODEL, "messages": messages}
    payload = {
    "model": config.OPENROUTER_MODEL,
    "messages": messages,
    "max_tokens": config.LLM_MAX_TOKENS,
}

    try:
        async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT_SECONDS) as client:
            res = await client.post(config.OPENROUTER_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise LLMError("The AI model took too long to respond", 504)
    except httpx.HTTPError:
        raise LLMError("Could not reach OpenRouter", 502)

    if res.status_code == 401:
        raise LLMError("OpenRouter rejected the API key", 502)
    if res.status_code == 402:
        raise LLMError("OpenRouter account has insufficient credits", 502)
    if res.status_code == 404:
        raise LLMError("Model not found. Check OPENROUTER_MODEL", 502)
    if res.status_code == 429:
        raise LLMError("The model is rate limited. Try again shortly", 429)
    if res.status_code != 200:
        raise LLMError(f"OpenRouter returned status {res.status_code}", 502)

    try:
        return res.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError):
        raise LLMError("Unexpected response format from the model", 502)