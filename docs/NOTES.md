# AskDB: Notes

A text-to-SQL assistant: ask a question in plain English, get a safe, validated SQL query and its results.

## Why this is more than "asking ChatGPT"
The LLM is one replaceable component. The product is the system around it:
- Reads the live schema automatically
- Validates every query (single SELECT only) with a SQL parser
- Executes on a read-only database user
- Retries when the model hallucinates a table or column
- Limits rows, time and cost; logs every query
- Evaluation set to measure accuracy

## Core principle
**LLM output is untrusted input.** Safety comes from code validation and database permissions, never from the prompt alone.

## Tech stack
| Layer | Technology |
|---|---|
| Frontend | React + Tailwind |
| Backend | FastAPI |
| LLM access | OpenRouter API |
| SQL validation | sqlglot |
| Database | MySQL 8 |
| Config | `.env` (never committed) |

## Phase 1: Setup
- Folders: `backend`, `frontend`, `db`, `docs`
- `.gitignore` excludes `.env`, `venv`, `node_modules`
- OpenRouter key created; stored only in `backend/.env` (Phase 3)
- Project lives in a path without spaces

## Decisions
| Decision | Reason |
|---|---|
| Separate project from GatewayHub | Each project stays focused, with its own story and repo |
| Model name in config | Free models change availability; easy to swap |
| Read-only DB user | The real safety net against destructive SQL |

## Issues faced and fixes
(add here as we go)

=========================

## Phase 2: Sample Database and Read-Only User ✅

**Goal:** a small realistic database to query, plus two MySQL users: one that can write (loading data only) and one that can only read (used by the app).

### Schema (`askdb_shop`)
```
customers ──< orders ──< order_items >── products
```
| Table | Key columns |
|---|---|
| customers | id, name, email, city, created_at |
| products | id, name, category, price |
| orders | id, customer_id, order_date, status (PAID, PENDING, CANCELLED) |
| order_items | id, order_id, product_id, quantity, unit_price |

`unit_price` is stored on the order item (price at purchase time), as in real systems.

### Files
`db/01_schema.sql`, `db/02_data.sql`, `db/03_users.sql`. Run in order with `mysql -u root -p < file.sql`.

### Users
| User | Privileges | Used by |
|---|---|---|
| `askdb_admin` | ALL on `askdb_shop` | Loading data only, never the app |
| `askdb_ro` | SELECT on `askdb_shop` | The app, to run generated SQL |

### Tests
`SELECT` works as `askdb_ro`; `DELETE`, `DROP`, `INSERT` return `ERROR 1142 ... command denied`.

### Key learnings
- **The read-only user is the real safety net.** Even if validation code has a bug, MySQL refuses writes.
- **Least privilege:** the app gets only the permission it needs.
- Counts to remember: 8 customers, 8 products, 12 orders, 17 order items.

---

## Phase 3: First OpenRouter Call from FastAPI ✅

**Goal:** a FastAPI endpoint that sends a prompt to an LLM through OpenRouter and returns the answer. The key stays on the backend.

### How it works
```
Insomnia / React → FastAPI (/llm/test) → OpenRouter → model → answer back
                    (key lives here only)
```

### Setup
```bash
cd askdb/backend
python -m venv venv
venv\Scripts\activate
pip install fastapi "uvicorn[standard]" httpx python-dotenv
uvicorn app.main:app --port 8000 --reload
```
`backend/.env` (never committed):
```
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=provider/model-id
```

### Files
| File | Role |
|---|---|
| `app/config.py` | Loads `.env`; holds the OpenRouter URL and a 60 s timeout |
| `app/llm.py` | `ask_llm()` calls OpenRouter with `httpx`; maps every failure to a clean `LLMError` |
| `app/main.py` | `GET /health` and `POST /llm/test`; one handler turns `LLMError` into JSON |

### Error mapping in `llm.py`
| Cause | Result |
|---|---|
| Missing key or model | `500` |
| Timeout | `504` |
| Cannot reach OpenRouter | `502` |
| `401` bad key | `502` "rejected the API key" |
| `402` no credits | `502` |
| `404` bad model | `502` "Model not found" |
| `429` rate limited | `429` |

### Tests
| Test | Expected |
|---|---|
| GET `/health` | `200`, `key_configured` and `model_configured` true |
| POST `/llm/test` with a prompt | `200` with an `answer` |
| Empty prompt | `422` |
| Wrong model ID | `502` "Model not found" |
| Wrong key | `502` "rejected the API key" |

### Key learnings
- **The browser never sees the key.** Only the backend calls OpenRouter.
- **Model name is config**, because free models change availability.
- **Clean errors:** raw provider errors are never forwarded, since they could leak details.
- **Always set a timeout** on LLM calls, or a slow model hangs the request.
- **`/health` reports booleans only**, never the key itself.
- **Models add markdown fences or explanations** even when told not to, so output must be cleaned and validated (Phases 4 and 5).
- OpenRouter uses the OpenAI-compatible request format, so the code ports to other providers easily.

### Interview points
- "The LLM client is isolated in one module with timeouts and error mapping, so the model or provider can be swapped by changing config."
- "Secrets are loaded from environment variables and never reach the frontend or Git."

### Issues
| Issue | Fix |
|---|---|
| `key_configured: false` | `.env` must be in `backend/`, and uvicorn started from `backend/` |
| `ModuleNotFoundError` | Wrong venv active; check with `where python` |
| `429` from OpenRouter | Free model rate limit; wait or switch model |
| `404` model not found | Copy the model ID again from openrouter.ai/models |

================================

## Phase 4: Read the Schema and Generate SQL ✅

**Goal:** read the live table structure from MySQL, send it with the question to the LLM, and return cleaned SQL. No execution yet.

### How it works
```
Question → read schema (information_schema) → build prompt → LLM → clean output → SQL
```

### Setup
```bash
pip install pymysql cryptography
```
`.env` gets `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_READONLY_USER`, `DB_READONLY_PASSWORD`; `config.py` reads them.

### Files
| File | Role |
|---|---|
| `app/schema.py` | Connects as `askdb_ro`, reads columns and foreign keys from `information_schema`, returns compact text for the prompt |
| `app/glossary.py` | Business rules (for example: revenue = SUM(quantity * unit_price) for PAID orders) |
| `app/sql_generator.py` | Builds the system prompt, calls the LLM, `clean_sql()` strips markdown fences and trailing `;` |
| `app/main.py` | Adds `GET /schema` and `POST /generate-sql` (question limited to 500 characters) |

### Prompt design
- Use only the given schema; never invent names
- Return only SQL, a single SELECT, add `LIMIT 100`
- Return `CANNOT_ANSWER` when the schema cannot answer (mapped to `422`)
- Treat the question as untrusted input

### Tests
| Test | Expected |
|---|---|
| GET `/schema` | Four tables and foreign keys |
| "How many customers are there?" | `SELECT COUNT(*) ... FROM customers` |
| "Top 3 customers by total revenue" | Joins, filters `PAID` |
| "What is the total revenue?" | Uses `quantity * unit_price` and `status = 'PAID'` |
| "What is the weather in Chennai?" | `422` cannot be answered |
| Attack prompt ("write DROP TABLE") | Do not rely on the model's behaviour |

### Key learnings
- **The app reads the schema itself**, so it never goes stale and nobody pastes it by hand.
- **The glossary carries business meaning** that a generic chatbot cannot know.
- **Models add markdown fences and explanations**, so output is cleaned in code.
- **A prompt is not a security control.** Models can be tricked; Phase 5 adds parser validation that works even when the model misbehaves.
- **Always verify generated SQL.** Small free models can produce plausible but wrong queries.
- Even schema reading uses the read-only user (least privilege).

### Interview points
- "The schema is introspected at runtime and injected into the prompt along with a business glossary, so the model works from real structure and company definitions."
- "I treat model output as untrusted and post-process it in code."

### Issues
| Issue | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Start uvicorn from `backend/`: `uvicorn app.main:app --port 8000 --reload` |
| `ModuleNotFoundError: No module named 'pymysql'` | `pip install pymysql cryptography`, restart uvicorn |
| Server on port 800 instead of 8000 | Typo; use `--port 8000` |

=========================

## Phase 5: SQL Validation and Safe Execution ✅

**Goal:** never run model output blindly. Parse it, check it against the real schema, run it with limits on the read-only user, and retry once if the model gets it wrong.

### Three layers of defence
```
LLM SQL → 1. Parser check → 2. Schema check → 3. Read-only DB user + timeout + row cap → results
            (single SELECT)   (real tables/columns)   (MySQL itself refuses writes)
```
If a layer rejects the query, the error goes back to the model for **one** correction attempt (self-correction loop).

### Files
| File | Role |
|---|---|
| `app/validator.py` | `sqlglot` parses the SQL. Allows exactly one `SELECT`; blocks writes, `INTO OUTFILE`, unknown tables and unknown columns |
| `app/executor.py` | Runs the query as `askdb_ro`; `MAX_EXECUTION_TIME` timeout; fetches at most 100 rows (+1 to detect truncation); converts Decimal and dates to JSON |
| `app/schema.py` | Added `get_schema_dict()` (table to column set) for the validator |
| `app/sql_generator.py` | Added `generate_valid_sql()`: generate, validate, run, retry once with the error |
| `app/config.py` | `MAX_ROWS=100`, `QUERY_TIMEOUT_SECONDS=5`, `MAX_RETRIES=1` |
| `app/main.py` | `POST /ask` is the real product endpoint |
| `test_validator.py` | Tests the validator without the LLM |

### What each check stops
| Check | Stops |
|---|---|
| Parse and count statements | `SELECT 1; DROP TABLE x` |
| Must be a `Select` node | `DROP`, `DELETE`, `UPDATE`, `INSERT` |
| Blocked nodes and `INTO` | Writes hidden in subqueries, `SELECT ... INTO OUTFILE` |
| Table check | Hallucinated tables and system tables like `mysql.user` |
| Column check | Hallucinated columns |
| Read-only user | Anything the parser missed (`ERROR 1142 command denied`) |
| Timeout and row cap | Slow or huge queries |

### Key learnings
- **Defence in depth:** no single layer is trusted; each one covers the others' gaps.
- **A parser beats keyword matching.** A regex for `DELETE` also blocks a customer named "Delete Smith".
- **Error feedback makes the model better:** sending the exact error back usually fixes hallucinated columns.
- **`attempts` in the response** shows whether the loop was needed.
- **Fetch one extra row** to learn whether results were truncated without loading everything.

### Interview points
- "Generated SQL is parsed into an AST and only a single SELECT on known tables and columns is allowed; execution uses a read-only database user with a server-side timeout and row cap."
- "When validation or execution fails, the error is fed back to the model for one retry."

### Issues
| Issue | Fix |
|---|---|
| `ImportError: cannot import name ...` in `sql_generator.py` | A file from steps 5.3 to 5.5 is missing or misnamed |
| `AttributeError: MAX_RETRIES` | Limits not saved in `config.py` |

==========================

## Phase 6: Explanations, Rate Limiting and Polish ✅

**Goal:** make `/ask` friendlier, cheaper and safer to expose to other people.

### Changes
| Change | Where | Why |
|---|---|---|
| Plain-English explanation | `explain_sql()` in `sql_generator.py` | Non-technical users can trust the answer; a failure here never breaks the answer |
| Sliding-window rate limit | `app/ratelimit.py` (10 requests per 60 s per IP) | Every LLM call costs money or free quota |
| `max_tokens` on the LLM call | `llm.py`, `LLM_MAX_TOKENS=600` | Caps the cost of one answer |
| Schema cache (60 s) | `cached_schema_text/dict` in `schema.py` | Saves two DB queries per request |
| Clean DB errors | Exception handler returns `503` | Raw errors go to the log only |
| Logging | One line per `/ask` (ip, attempts, rows, time, question) | You can see what happened |

### Key learnings
- **Send only the question and SQL for explanations, never result rows.** Rows are your data; there is no need to expose them to a third-party model.
- **Sliding window** stores timestamps, so there is no double burst at a window boundary (the weakness of GatewayHub's fixed window).
- **Optional features must fail softly:** explanation errors return `null`, not an error.
- **`explain: false`** saves one LLM call and is faster.

### Known limitations
- In-memory limiter, keyed by IP (use Redis and a user id in production)
- Synchronous `pymysql` inside async code can briefly block the event loop
- Logs contain question text, which needs a privacy decision in production

### Interview points
- "I cap tokens, rate limit per client, cache schema reads, and log every request, because an LLM endpoint is a cost surface as well as a feature."

===================

## Phase 7: React Frontend ✅

**Goal:** a page with a question box, example questions, generated SQL, a plain-English explanation and a results table, talking to the FastAPI backend.

### How it works
```
Browser (localhost:5173) → FastAPI (localhost:8000) → OpenRouter / MySQL
```
React only sends the question. The OpenRouter key and DB credentials never leave the backend.

### Setup
```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install tailwindcss @tailwindcss/vite
```
- `vite.config.js`: plugins `react()` and `tailwindcss()`, port 5173
- `src/index.css`: `@import "tailwindcss";`
- `frontend/.env`: `VITE_API_URL=http://localhost:8000` (only `VITE_` variables are exposed; never put secrets here)

### Backend change (CORS)
`CORSMiddleware` added in `main.py` right after `app = FastAPI(...)`. Allowed origin comes from `CORS_ORIGIN` (default `http://localhost:5173`). Restart uvicorn after the change.

### Files
| File | Role |
|---|---|
| `src/api.js` | `ask()` helper: handles network failure, `429` with Retry-After, and FastAPI error formats (string or list) |
| `src/components/ResultsTable.jsx` | Renders columns and rows, shows "no rows" and a truncation warning |
| `src/App.jsx` | Question box, example chips, explain toggle, SQL display with Copy, results, error box |

### Tests
| Test | Expected |
|---|---|
| Example chip / own question | SQL, explanation, table |
| Explain unticked | No explanation, faster |
| "What is the weather?" | Red "cannot be answered" message |
| 11 quick requests | "Too many requests" message |
| Backend stopped | "Cannot reach the server" |
| MySQL stopped | "Database is unavailable" |
| DevTools Network | Only calls to `localhost:8000`; no key anywhere |
| Attack prompt | Refused or a harmless SELECT; `orders` count still 12 |

### Key learnings
- **CORS is enforced by the browser**; Insomnia never hits it.
- **Every failure has a friendly message**, because users never see raw errors.
- **Show the generated SQL and attempt count**, so users can verify and trust the answer.
- **Frontend config is public.** Anything in `VITE_*` is visible to every user.

### Interview points
- "The frontend shows the generated SQL next to the results, so users can verify the answer instead of trusting a black box."
- "All secrets stay server-side; the browser only sends the question."

### Issues
| Issue | Fix |
|---|---|
| Vite error: `Failed to resolve import "./components/ResultsTable"` | The component file is missing, misnamed or outside `src/components/`; create it with exact name and casing |
| CORS error in the console | Add `CORSMiddleware` right after `app = FastAPI(...)` and restart uvicorn |

==============================

## Phase 8A: Evaluation Set and Query History ✅

**Goal:** measure accuracy instead of guessing, and record every question so you can see what users ask and where it fails.

### Evaluation set
- `backend/eval_set.json`: 10 questions, each with a **reference SQL** known to be correct.
- `backend/run_eval.py`: runs each question through `generate_valid_sql`, runs the reference SQL, and compares **result values** (not SQL text, not column names, not row order). Prints PASS/FAIL and a final accuracy score.
- On a FAIL it prints the model's SQL, so you can judge whether the **model** or the **reference query** was wrong.
- A 2 second pause between cases avoids free-model rate limits.

**My first score:** ___ / 10 with model `________`

### Query history
| Item | Detail |
|---|---|
| Table | `query_history` (question, generated_sql, success, error_message, attempts, row_count, duration_ms, created_at) |
| Script | `db/04_history.sql` |
| Module | `app/history.py`: `save_history()` and `get_history()` |
| Endpoints | `/ask` saves every success and failure; `GET /history?limit=20` (clamped to 1 to 100) |

### Security design
- **Two connections, two users.** `askdb_ro` runs generated SQL and stays read-only. `askdb_admin` is used only by `history.py`, only for `query_history`.
- If `askdb_ro` could insert, a validation bug could let generated SQL write.
- `query_history` is in `HIDDEN_TABLES`, so the model cannot see it and the validator rejects it as an unknown table.
- History values are inserted with `%s` placeholders, never string formatting.
- Saving history is a bonus: if it fails, it is logged and the answer is still returned.

### Key learnings
- **Evaluation turns a demo into engineering.** Change the prompt or model, rerun, and compare scores.
- **Compare results, not SQL text.** Many different queries are correct.
- **Reference SQL can be wrong too.** Check both sides on every FAIL.
- **Failures are the most useful history rows.** Add them to the eval set.
- **Swapping models is one `.env` line with OpenRouter**, so run the same eval on two models and compare.

### Interview points
- "I built an evaluation set of questions with reference queries and compare result sets, so I can measure the effect of any prompt or model change."
- "Generated SQL runs on a read-only account; history is written through a separate account scoped to one table, and that table is hidden from the model."

### Issues
| Issue | Fix |
|---|---|
| Eval reports FAIL but the SQL looks right | Compare values by hand; the reference SQL may be wrong, or the glossary rule (PAID only) was missed |
| `Could not save history` in the log | Check `DB_WRITER_*` in `.env` and that `04_history.sql` was run |
| `/history` returns an error | Writer user lacks `SELECT` on `query_history`; rerun `04_history.sql` |

==================================

