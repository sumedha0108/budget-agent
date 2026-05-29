from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, validator
from langchain_core.messages import HumanMessage
import asyncio

from app.graph.main_graph import build_graph
from app.telegram_bot import build_telegram_app

graph = None
telegram_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, telegram_app

    try:
        graph = await build_graph()
        print("✅ Graph ready")

        telegram_app = build_telegram_app(graph)
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("✅ Telegram bot running")

    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

    yield

    # clean shutdown
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    msg: str
    user_id: str = "user_1"

    @validator("msg")
    def msg_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 1000:
            raise ValueError("Message too long (max 1000 chars)")
        return v.strip()


@app.post("/chat")
async def chat(req: ChatRequest):
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    try:
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=req.msg)],
                "user_id": req.user_id
            },
            config={
                "configurable": {
                    "thread_id": req.user_id,
                    "user_id": req.user_id
                },
                "recursion_limit": 10
            }
        )
        return {"response": result["messages"][-1].content}
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR] /chat failed: {error_str}")

        if "tool call validation failed" in error_str:
            return JSONResponse(
                status_code=422,
                content={"error": "I couldn't understand the values you provided. Please check the amount and try again."}
            )

        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")



@app.get("/health")
async def health():
    return {"status": "ok", "graph": graph is not None}


@app.get("/summary/{user_id}")
async def summary(user_id: str):
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    try:
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="analyze my spending and give me a full financial health report with recommendations")],
                "user_id": user_id
            },
            config={
                "configurable": {
                    "thread_id": f"{user_id}_summary",
                    "user_id": user_id
                },
                "recursion_limit": 10
            }
        )
        return {"summary": result["messages"][-1].content}
    except Exception as e:
        print(f"[ERROR] {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})