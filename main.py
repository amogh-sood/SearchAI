import asyncio
import os
from dotenv import load_dotenv
from fastmcp import Client
from langchain.agents import AgentType, initialize_agent
from langchain_community.tools import Tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import concurrent.futures
from collections.abc import AsyncGenerator

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server

# ------------------------ setup ------------------------
server = Server()
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

MCP_SERVER_URL = "http://localhost:8000/mcp/"

# ---- your MCP tool bridges (kept) ----
def call_mcp_tool(tool_name, payload):
    async def _call():
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(tool_name, payload)
            return result.data if hasattr(result, "data") else str(result)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: asyncio.run(_call()))
        return future.result()

def web_crawl_tool_func(query):
    return call_mcp_tool("web_crawl_tool", {"query": query})

def yahoo_finance_tool_func(ticker):
    return call_mcp_tool("yahoo_finance_tool", {"ticker": ticker})

def hello_tool_func(name):
    return call_mcp_tool("hello_tool", {"name": name})

# You had these defined; we keep them for LangChain agent use:
tools = [
    Tool(
        name="web_crawl_tool",
        func=web_crawl_tool_func,
        description="Searches the web and crawls the top result using FireCrawl."
    ),
    Tool(
        name="hello_tool",
        func=hello_tool_func,
        description="Returns a hello message from the MCP server"
    ),
    Tool(
        name="yahoo_finance_tool",
        func=yahoo_finance_tool_func,
        description="Fetches the latest price for a given ticker using Yahoo Finance."
    ),
]

llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o-mini",
    api_key=SecretStr(OPENAI_API_KEY)
)

# Optional: a LangChain agent that can use your MCP tools
lc_agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
)

# -------------------- helpers --------------------
def _extract_text(input_msgs: list[Message]) -> str:
    """Concatenate all string contents from Message.parts."""
    out: list[str] = []
    for msg in input_msgs or []:
        for part in (msg.parts or []):
            if isinstance(part, MessagePart) and isinstance(part.content, str):
                out.append(part.content)
    return " ".join(out).strip()

def _maybe_upper_ticker(text: str) -> str | None:
    """Heuristic ticker grab: skip common uppercase words; map vendor names."""
    STOP = {"CEO", "CFO", "CTO", "USD", "A", "AN", "THE", "IS", "OF", "FOR"}
    lower = text.lower()
    if "nvidia" in lower:
        return "NVDA"
    for tok in text.replace(",", " ").split():
        if tok.isalpha() and tok.isupper() and 1 <= len(tok) <= 6 and tok not in STOP:
            return tok
    return None

# --------------------- agents ---------------------
@server.agent(name="agent")
async def agent(input: list[Message], context: Context) -> AsyncGenerator[str, None]:
    """
    General agent:
      - If it looks like a ticker, call MCP yahoo_finance_tool.
      - If it starts with 'hello', call MCP hello_tool.
      - If it includes 'crawl:' prefix, call MCP web_crawl_tool on the rest.
      - Else: answer with LC agent (uses your MCP-backed tools if needed), fallback to echo.
    """
    text = _extract_text(input)
    if not text:
        yield "(empty input)"
        return

    # 1) finance ticker
    maybe = _maybe_upper_ticker(text)
    if maybe:
        try:
            res = yahoo_finance_tool_func(maybe)
            yield str(res)
            return
        except Exception as e:
            yield f"[agent] MCP finance error: {e}"

    # 2) hello tool
    if text.lower().startswith("hello"):
        name = text.split(maxsplit=1)[1] if len(text.split()) > 1 else "there"
        try:
            res = hello_tool_func(name)
            yield str(res)
            return
        except Exception as e:
            yield f"[agent] MCP hello error: {e}"

    # 3) web crawl (simple syntax: "crawl: <query>")
    if "crawl:" in text.lower():
        query = text.split("crawl:", 1)[1].strip()
        if query:
            try:
                res = web_crawl_tool_func(query)
                yield str(res)
                return
            except Exception as e:
                yield f"[agent] MCP crawl error: {e}"

    # 4) try LC agent to reason w/ your tools
    try:
        # LC wants a string prompt; it can call our Tool funcs above if it decides to
        lc_resp = lc_agent.run(text)
        yield str(lc_resp)
        return
    except Exception:
        # 5) fallback: echo
        yield f"agent received: {text}"

@server.agent(name="dateAgent")
async def dateAgent(input: list[Message], context: Context) -> AsyncGenerator[str, None]:
    """Return the current date in YYYY-MM-DD."""
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    yield f"Current date is: {current_date}"

# --------------------- run ---------------------
if __name__ == "__main__":
    server.run(port=8002)