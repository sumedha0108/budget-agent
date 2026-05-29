# Budget Agent

A multi-agent personal finance assistant built with LangGraph, FastAPI, and Telegram.

## Architecture
- **Supervisor** — LLM-based orchestrator that routes and chains agents
- **5 Specialized Agents** — expense, analytics, planner, split, debt
- **Persistent Memory** — Postgres checkpointer across sessions
- **Telegram Bot** — real interface with automatic user isolation

## Stack
- LangGraph + LangChain
- FastAPI
- PostgreSQL
- Groq (Llama 4 Scout)
- python-telegram-bot

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
uvicorn app.server:app --reload
```

## Endpoints
- `POST /chat` — main chat endpoint
- `GET /summary/{user_id}` — financial health report
- `GET /health` — health check