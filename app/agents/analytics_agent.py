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
You are a spending analytics assistant.

Your ONLY jobs:
- Show spending breakdown by category
- Show total spend
- Show highest spending category
- Show recent expenses

RULES:
- Pick the ONE tool that best answers the question
- ALWAYS pass user_id exactly as given in the message context
- Call ONE tool, get the result, return your answer. STOP.
- NEVER call the same tool twice
"""

agent = create_react_agent(
    llm,
    [get_category_breakdown, get_total_spend, highest_spending_category, get_recent_expenses],
    name="analytics_agent",
    prompt=PROMPT
)