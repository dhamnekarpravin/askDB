import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT_SECONDS = 60


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_READONLY_USER = os.getenv("DB_READONLY_USER")
DB_READONLY_PASSWORD = os.getenv("DB_READONLY_PASSWORD")

MAX_ROWS = 100
QUERY_TIMEOUT_SECONDS = 5
MAX_RETRIES = 1

RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_SECONDS = 60
SCHEMA_CACHE_SECONDS = 60
LLM_MAX_TOKENS = 600

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")


DB_WRITER_USER = os.getenv("DB_WRITER_USER")
DB_WRITER_PASSWORD = os.getenv("DB_WRITER_PASSWORD")