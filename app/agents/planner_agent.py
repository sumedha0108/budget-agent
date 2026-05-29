from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.analytics import (
    get_category_breakdown,
    get_total_spend,
    highest_spending_category,
    get_recent_expenses
)
from app.config import settings

llm = ChatGroq(model=settings.MODEL_NAME, temperature=0, api_key=settings.GROQ_API_KEY)

PROMPT = """
You are a financial planning assistant.

Your job:
- Look at the user's spending data
- Identify where they are overspending
- Give 2-3 concrete, actionable recommendations

RULES:
- Call get_category_breakdown first to understand spending
- You may call ONE more tool if needed for more context
- NEVER call more than 2 tools total
- ALWAYS pass user_id exactly as given in the message context
- After tools return results, give your recommendations. STOP.
"""

agent = create_react_agent(
    llm,
    [get_category_breakdown, get_total_spend, highest_spending_category, get_recent_expenses],
    name="planner_agent",
    prompt=PROMPT
)