from langchain_core.tools import tool
from app.db import get_conn
from langchain_core.runnables import RunnableConfig


@tool
def add_debt(lender: str, borrower: str, amount: float, description: str, config: RunnableConfig) -> str:
    """Record that someone owes money.

    Args:
        lender: person who paid / is owed money
        borrower: person who owes money
        amount: amount owed in INR
        description: what the debt is for
    """

    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO debts (user_id, lender, borrower, amount, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, lender, borrower, amount, description))
            conn.commit()
        return f"Recorded: {borrower} owes {lender} ₹{amount} for {description}"
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def settle_debt(borrower: str, amount: float, config: RunnableConfig) -> str:
    """Mark a debt as settled (paid back).

    Args:
        borrower: person who is paying back
        amount: amount being paid back in INR
    """

    try:

        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, amount FROM debts
                    WHERE borrower = %s AND user_id = %s AND settled = FALSE
                    ORDER BY created_at ASC
                """, (borrower, user_id))
                rows = cur.fetchall()

                remaining = amount
                for debt_id, debt_amount in rows:
                    if remaining <= 0:
                        break
                    if remaining >= debt_amount:
                        cur.execute("UPDATE debts SET settled = TRUE, amount = 0 WHERE id = %s", (debt_id,))
                        remaining -= debt_amount
                    else:
                        cur.execute("UPDATE debts SET amount = amount - %s WHERE id = %s", (remaining, debt_id))
                        remaining = 0

            conn.commit()
        return f"{borrower} settled ₹{amount}"
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


@tool
def get_pending_debts(config: RunnableConfig) -> str:
    """Get all unsettled debts for a user — who owes them money."""

    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT lender, borrower, amount, description
                    FROM debts
                    WHERE user_id = %s AND settled = FALSE
                    ORDER BY created_at ASC
                """, (user_id,))
                rows = cur.fetchall()

        if not rows:
            return "No pending debts."

        output = []
        total = 0
        for lender, borrower, amount, desc in rows:
            total += amount
            output.append(f"{borrower} owes {lender} ₹{amount} ({desc})")
        output.append(f"\nTotal outstanding: ₹{total}")
        return "\n".join(output)
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"


# tools/debts.py — add this new tool
@tool
def log_my_share(
    amount: float,
    description: str,
    config: RunnableConfig
) -> str:
    """
    Log the user's own share of a split expense into personal expenses.
    Call this ONCE after all add_debt calls are done.
    """

    try:
        user_id = config["configurable"].get("user_id", "default")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO expenses (user_id, description, amount, category)
                    VALUES (%s, %s, %s, 'other')
                """, (user_id, description, amount))
            conn.commit()

        return f"Your share of ₹{amount} for {description} logged."
    except ValueError:
        return "Invalid amount — please provide a number."
    except RuntimeError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Unexpected error logging expense: {e}"