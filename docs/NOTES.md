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

