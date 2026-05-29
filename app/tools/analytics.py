from langchain_core.tools import tool
from app.db import get_conn
from langchain_core.runnables import RunnableConfig


@tool
def get_category_breakdown(config: RunnableConfig) -> str:
    """Get spending grouped by category for a user.
    """
    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT category, SUM(amount)
                    FROM expenses
                    WHERE user_id = %s
                    GROUP BY category
                    ORDER BY SUM(amount) DESC
                """, (user_id,))
                rows = cur.fetchall()

        if not rows:
            return "No expenses found."

        return "\n".join([f"{cat}: ₹{amt}" for cat, amt in rows])
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def get_total_spend(config: RunnableConfig) -> str:
    """Get total spend across all expenses."""

    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT SUM(amount) FROM expenses
                    WHERE user_id = %s
                """, (user_id,))
                total = cur.fetchone()[0] or 0
        return f"Total spend: ₹{total}"
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def highest_spending_category(config: RunnableConfig) -> str:
    """Find the highest spending category."""
    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT category, SUM(amount) as total
                    FROM expenses
                    WHERE user_id = %s
                    GROUP BY category
                    ORDER BY total DESC
                    LIMIT 1
                """, (user_id,))
                row = cur.fetchone()

        if not row:
            return "No expenses found."
        return f"Highest spending: {row[0]} ₹{row[1]}"
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def get_recent_expenses(config: RunnableConfig, limit: int = 5) -> str:
    """Get recent expenses. limit: how many to fetch (default 5)."""

    try:
        user_id = config["configurable"].get("user_id", "default")
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT description, amount, category
                    FROM expenses
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                rows = cur.fetchall()

        if not rows:
            return "No expenses found."

        return "\n".join([f"{desc} | ₹{amt} | {cat}" for desc, amt, cat in rows])
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"