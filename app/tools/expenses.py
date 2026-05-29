from langchain_core.tools import tool
from app.db import get_conn
from langchain_core.runnables import RunnableConfig


@tool
def add_expense(description: str, amount: float, category: str, config: RunnableConfig) -> str:
    """Add a personal expense for a user.

    Args:
        description: what was spent on
        amount: amount in INR as a number
        category: one of food, transport, groceries, entertainment, utilities, health, other
    """
    try:
        user_id = config["configurable"].get("user_id", "default")

        valid_categories = ["food", "transport", "groceries", "entertainment", "utilities", "health", "other"]
        if category not in valid_categories:
            category = "other"

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO expenses (user_id, description, amount, category) VALUES (%s, %s, %s, %s)",
                    (user_id, description, amount, category),
                )
            conn.commit()
        return f"Logged: {description} ₹{amount} [{category}]"
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def get_monthly_spend(config: RunnableConfig) -> str:
    """Get total spending this month for a user."""
    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT SUM(amount) FROM expenses
                    WHERE user_id = %s
                    AND created_at >= date_trunc('month', CURRENT_DATE)
                """, (user_id,))
                total = cur.fetchone()[0] or 0
        return f"Total spent this month: ₹{total}"

    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"