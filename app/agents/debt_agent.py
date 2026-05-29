from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.debts import settle_debt, get_pending_debts
from app.config import settings

llm = ChatGroq(model=settings.MODEL_NAME, temperature=0, api_key=settings.GROQ_API_KEY)

PROMPT = """
You are a debt management assistant.

Your ONLY jobs:
- Settle a debt when someone says they paid back money
- Show pending debts when asked who owes what

RULES:
- Call settle_debt when user says: paid back, repaid, settled, returned money
- Call get_pending_debts when user asks who owes them or what debts are pending
- ALWAYS pass user_id exactly as given in the message context
- Call ONE tool, get the result, return your answer. STOP.
- NEVER call a tool twice
- NEVER call get_pending_debts before or after settle_debt in the same turn
"""

agent = create_react_agent(
    llm,
    [settle_debt, get_pending_debts],
    name="debt_agent",
    prompt=PROMPT
)