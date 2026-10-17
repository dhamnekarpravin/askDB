from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import config
from .llm import LLMError, ask_llm

app = FastAPI(title="AskDB")


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


@app.exception_handler(LLMError)
async def llm_error_handler(request, exc: LLMError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "askdb",
        "model_configured": bool(config.OPENROUTER_MODEL),
        "key_configured": bool(config.OPENROUTER_API_KEY),
    }


@app.post("/llm/test")
async def llm_test(request: PromptRequest):
    answer = await ask_llm(request.prompt)
    return {"model": config.OPENROUTER_MODEL, "answer": answer}