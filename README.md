# Budget Agent

A multi-agent personal finance assistant with a supervisor-based architecture, persistent memory, and an MCP server for tool interoperability.

## Architecture

The system has three layers:

**Interfaces** — Telegram bot, FastAPI REST, and Claude Desktop (via MCP) all feed into the same backend.

**Agent layer** — A supervisor LLM decides which agents to call and in what order. For complex queries (e.g. "analyze my spending and suggest improvements") it chains analytics → planner and synthesizes a single response. Five specialized agents handle distinct domains: expense logging, analytics, financial planning, bill splitting, and debt settlement.

**Tool layer** — Exposed both as LangChain tools (used by agents) and as a standalone MCP server (used by Claude Desktop and any other MCP client).

<img width="720" height="595" alt="image" src="https://github.com/user-attachments/assets/9ae255c1-3ea1-42c6-89d6-63db5672dca6" />


## Stack

- **LangGraph** — agent orchestration and state management
- **LangChain** — tool definitions and LLM bindings
- **FastAPI** — REST interface
- **PostgreSQL** — persistent storage + LangGraph checkpointer (conversation memory)
- **Groq** — LLM inference (Llama 4 Scout)
- **python-telegram-bot** — Telegram interface
- **FastMCP** — MCP server

## Features

- Multi-agent orchestration with LLM-based supervisor (no keyword routing)
- Agent chaining — analytics feeds into planner for complex queries
- Persistent conversation memory across server restarts (Postgres checkpointer)
- Per-user data isolation via `RunnableConfig`
- MCP server — tools usable from Claude Desktop or any MCP client
- `/summary/{user_id}` endpoint — on-demand financial health report
- Input validation and structured error handling

## Setup

```bash
git clone https://github.com/sumedha0108/budget-agent
cd budget-agent
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
```

Create the database tables using postgresql:
```sql
CREATE TABLE expenses (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR NOT NULL,
  description TEXT,
  amount NUMERIC,
  category VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE debts (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR NOT NULL,
  lender VARCHAR,
  borrower VARCHAR,
  amount NUMERIC,
  description TEXT,
  settled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

Start the server:
```bash
uvicorn app.server:app --reload
```

Start the MCP server (separate terminal):
```bash
python app/mcp_server.py
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send a message `{"msg": "...", "user_id": "..."}` |
| GET | `/summary/{user_id}` | Financial health report |
| GET | `/health` | Health check |

## MCP Server (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "budget-agent": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/budget-agent/app/mcp_server.py"]
    }
  }
}
```

Claude Desktop will discover all financial tools automatically.


## Environment Variables

```
GROQ_API_KEY=
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
TELEGRAM_TOKEN=
```
