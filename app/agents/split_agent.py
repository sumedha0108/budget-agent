from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.debts import add_debt, get_pending_debts, log_my_share
from app.config import settings

llm = ChatGroq(model=settings.MODEL_NAME, temperature=0, api_key=settings.GROQ_API_KEY)

PROMPT = """
You are a split expense assistant.

RULES:
- payer is always "User" unless a real name is explicitly stated
- participants are the OTHER people (never include the payer)
- split_amount = total_amount / (number of participants + 1)

STEPS (always follow this order):
1. Call add_debt once for EACH participant
2. Call log_my_share ONCE with the same split_amount and description
3. Summarize and STOP

EXAMPLE:
User: "I paid 3000 for dinner with Rahul and Priya"
→ split_amount = 3000 / 3 = 1000
→ add_debt(lender="User", borrower="Rahul", amount=1000, description="dinner")
→ add_debt(lender="User", borrower="Priya", amount=1000, description="dinner")
→ log_my_share(amount=1000, description="dinner")
→ "Rahul and Priya each owe you ₹1000 for dinner. Your share of ₹1000 has been logged."

NEVER call get_pending_debts in the same turn as add_debt or log_my_share.
"""


agent = create_react_agent(
    llm,
    [add_debt, get_pending_debts, log_my_share],
    name="split_agent",
    prompt=PROMPT
)