import logging
import time

import pymysql
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import config
from .llm import LLMError, ask_llm
from .ratelimit import rate_limit
from .schema import get_schema_text
from .sql_generator import explain_sql, generate_sql, generate_valid_sql

from fastapi.middleware.cors import CORSMiddleware

from .history import get_history, save_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("askdb")

app = FastAPI(title="AskDB")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ORIGIN],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

class PromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskRequest(QuestionRequest):
    explain: bool = True


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(pymysql.err.MySQLError)
async def db_error_handler(request: Request, exc: pymysql.err.MySQLError):
    log.error("Database error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "Database is unavailable"})


@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "askdb",
        "model_configured": bool(config.OPENROUTER_MODEL),
        "key_configured": bool(config.OPENROUTER_API_KEY),
    }


@app.get("/schema")
def schema():
    return {"schema": get_schema_text()}


@app.post("/llm/test", dependencies=[Depends(rate_limit)])
async def llm_test(request: PromptRequest):
    answer = await ask_llm(request.prompt)
    return {"model": config.OPENROUTER_MODEL, "answer": answer}


@app.post("/generate-sql", dependencies=[Depends(rate_limit)])
async def generate(request: QuestionRequest):
    sql = await generate_sql(request.question)
    return {"question": request.question, "sql": sql}

@app.post("/ask", dependencies=[Depends(rate_limit)])
async def ask(request: AskRequest, http: Request):
    start = time.time()
    ip = http.client.host if http.client else "unknown"

    try:
        result = await generate_valid_sql(request.question)
    except LLMError as e:
        duration = int((time.time() - start) * 1000)
        log.warning("ask FAILED ip=%s status=%s reason=%s question=%r",
                    ip, e.status_code, e.message, request.question)
        save_history(request.question, None, False, e.message, None, None, duration)
        raise

    explanation = await explain_sql(request.question, result["sql"]) if request.explain else None

    duration = int((time.time() - start) * 1000)
    log.info("ask OK ip=%s attempts=%s rows=%s time=%.1fs question=%r",
             ip, result["attempts"], result["row_count"], duration / 1000, request.question)
    save_history(request.question, result["sql"], True, None,
                 result["attempts"], result["row_count"], duration)

    return {"question": request.question, "explanation": explanation, **result}


@app.get("/history")
def history(limit: int = 20):
    return {"items": get_history(min(max(limit, 1), 100))}