# app/agents/supervisor.py
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.config import settings
import json

llm = ChatGroq(
    model=settings.SUPERVISOR_MODEL,  # use stronger model for supervisor
    temperature=0,
    api_key=settings.GROQ_API_KEY
)

SUPERVISOR_PROMPT = """You are a supervisor for a personal finance assistant.

Available agents:
- expense    → log personal spending
- analytics  → spending summaries, breakdowns, trends
- planner    → budget advice, recommendations, financial health
- split      → split bills with others
- debt       → settle debts, check who owes what

Your job: given the user message, return a JSON plan.

SIMPLE queries (one clear intent) → single agent:
{"agents": ["expense"], "mode": "single"}

COMPLEX queries (multiple intents or needs context from another agent) → chain:
{"agents": ["analytics", "planner"], "mode": "chain"}

Rules:
- "analyze and suggest" or "how can I improve" → ["analytics", "planner"], chain
- "split dinner" → ["split"], single
- "who owes me" → ["debt"], single  
- "I spent" → ["expense"], single
- "how much did I spend" → ["analytics"], single
- For chain mode, first agent's output is passed as context to the next

Return ONLY valid JSON. No explanation.
"""

def supervisor_plan(message: str) -> dict:
    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=message)
    ])
    
    try:
        plan = json.loads(response.content.strip())
        # validate
        valid_agents = {"expense", "analytics", "planner", "split", "debt"}
        agents = plan.get("agents", ["expense"])
        agents = [a for a in agents if a in valid_agents]
        if not agents:
            agents = ["expense"]
        return {
            "agents": agents,
            "mode": plan.get("mode", "single")
        }
    except Exception:
        return {"agents": ["expense"], "mode": "single"}