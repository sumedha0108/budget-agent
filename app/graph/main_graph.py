from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.expense_agent import agent as expense_agent
from app.agents.analytics_agent import agent as analytics_agent
from app.agents.planner_agent import agent as planner_agent
from app.agents.split_agent import agent as split_agent
from app.agents.debt_agent import agent as debt_agent

from app.config import settings
import time


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str


async def expense_node(state):
    print("ROUTED TO → EXPENSE AGENT")
    user_id = state["user_id"]
    messages = [SystemMessage(content=f"The user_id for all tool calls is: {user_id}")] + state["messages"]
    start = time.time()
    result = await expense_agent.ainvoke({"messages": messages},  # 👈 no SystemMessage injection
        config={
            "configurable": {
                "user_id": state["user_id"]  # 👈 user_id flows via config only
            }
        })
    print(f"[expense_agent] completed in {time.time()-start:.2f}s")
    return {"messages": result["messages"]}


async def analytics_node(state):
    print("ROUTED TO → ANALYTICS AGENT")
    user_id = state["user_id"]
    messages = [SystemMessage(content=f"The user_id for all tool calls is: {user_id}")] + state["messages"]
    start = time.time()
    result = await analytics_agent.ainvoke({"messages": messages},  # 👈 no SystemMessage injection
        config={
            "configurable": {
                "user_id": state["user_id"]  # 👈 user_id flows via config only
            }
        })
    print(f"[analytics_agent] completed in {time.time()-start:.2f}s")
    return {"messages": result["messages"]}


async def planner_node(state):
    print("ROUTED TO → PLANNER AGENT")
    user_id = state["user_id"]
    messages = [SystemMessage(content=f"The user_id for all tool calls is: {user_id}")] + state["messages"]
    start = time.time()
    result = await planner_agent.ainvoke({"messages": messages},  # 👈 no SystemMessage injection
        config={
            "configurable": {
                "user_id": state["user_id"]  # 👈 user_id flows via config only
            }
        })
    print(f"[planner_agent] completed in {time.time()-start:.2f}s")
    return {"messages": result["messages"]}


async def split_node(state):
    print("ROUTED TO → SPLIT AGENT")
    user_id = state["user_id"]
    messages = [SystemMessage(content=f"The user_id for all tool calls is: {user_id}")] + state["messages"]
    start = time.time()
    result = await split_agent.ainvoke({"messages": messages},  # 👈 no SystemMessage injection
        config={
            "configurable": {
                "user_id": state["user_id"]  # 👈 user_id flows via config only
            }
        })
    print(f"[split_agent] completed in {time.time()-start:.2f}s")
    return {"messages": result["messages"]}


async def debt_node(state):
    print("ROUTED TO → DEBT AGENT")
    user_id = state["user_id"]
    messages = [SystemMessage(content=f"The user_id for all tool calls is: {user_id}")] + state["messages"]
    start = time.time()
    result = await debt_agent.ainvoke({"messages": messages},  # 👈 no SystemMessage injection
        config={
            "configurable": {
                "user_id": state["user_id"]  # 👈 user_id flows via config only
            }
        })
    print(f"[debt_agent] completed in {time.time()-start:.2f}s")
    return {"messages": result["messages"]}

AGENT_NODES = {
    "expense": expense_node,
    "analytics": analytics_node,
    "planner": planner_node,
    "split": split_node,
    "debt": debt_node,
}

async def supervisor_node(state):
    from app.agents.supervisor import supervisor_plan, llm  # 👈 import llm too
    
    last_msg = state["messages"][-1].content
    plan = supervisor_plan(last_msg)
    
    print(f"[SUPERVISOR] plan → {plan}")
    
    agents = plan["agents"]
    mode = plan["mode"]
    
    if mode == "single" or len(agents) == 1:
        node_fn = AGENT_NODES[agents[0]]
        return await node_fn(state)
    
    # chain mode
    current_state = state
    all_outputs = []
    
    for agent_name in agents:
        node_fn = AGENT_NODES[agent_name]
        result = await node_fn(current_state)
        
        last_response = result["messages"][-1].content
        all_outputs.append(f"[{agent_name}]: {last_response}")
        
        context_msg = SystemMessage(
            content=f"Previous agent output (use as context):\n{last_response}"
        )
        current_state = {
            **current_state,
            "messages": current_state["messages"] + [context_msg]
        }
    
    # 👇 synthesis — replaces the raw concatenated output
    combined = "\n\n".join(all_outputs)
    
    synthesis = llm.invoke([
        SystemMessage(content="""You are a financial assistant. 
Two specialized agents have analyzed the user's finances.
Combine their outputs into ONE clean, helpful response.
- No agent labels like [analytics] or [planner]
- No repetition
- Be concise but actionable
- Use bullet points only if it genuinely helps clarity"""),
        HumanMessage(content=f"User asked: {last_msg}\n\nAgent outputs:\n{combined}")
    ])
    
    return {"messages": [AIMessage(content=synthesis.content)]}

builder = StateGraph(AgentState)

builder.add_node("expense", expense_node)
builder.add_node("analytics", analytics_node)
builder.add_node("planner", planner_node)
builder.add_node("split", split_node)
builder.add_node("debt", debt_node)
builder.add_node("supervisor", supervisor_node)

builder.set_entry_point("supervisor")

builder.add_edge("expense", END)
builder.add_edge("analytics", END)
builder.add_edge("planner", END)
builder.add_edge("split", END)
builder.add_edge("debt", END)
builder.add_edge("supervisor", END)


checkpointer_instance = None

async def build_graph():
    global checkpointer_instance
    
    pool = AsyncConnectionPool(
        conninfo=settings.DATABASE_URL,
        max_size=10,
        open=False,
        kwargs={"autocommit": True}
    )
    await pool.open()
    
    checkpointer_instance = AsyncPostgresSaver(pool)
    await checkpointer_instance.setup()
    
    return builder.compile(checkpointer=checkpointer_instance)