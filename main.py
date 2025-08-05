import asyncio
import os
from dotenv import load_dotenv
from fastmcp import Client
from langchain.agents import AgentType, initialize_agent
from langchain_community.tools import Tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import concurrent.futures
import yfinance as yf




load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

MCP_SERVER_URL = "http://localhost:8000/mcp/"

def call_mcp_tool(tool_name, payload):
    async def _call():
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(tool_name, payload)
            return result.data if hasattr(result, 'data') else str(result)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: asyncio.run(_call()))
        return future.result()

def web_crawl_tool_func(query):
    return call_mcp_tool("web_crawl_tool", {"query": query})

def yahoo_finance_tool_func(ticker):
    return call_mcp_tool("yahoo_finance_tool", {"ticker": ticker})

def embedder_tool_func(text):
    return call_mcp_tool("embedder_tool", {"text": text})

def similarity_search_tool_func(query):
    return call_mcp_tool("similarity_search_tool", {
        "query": query,
        "documents": [
            "AI refers to machines that mimic human intelligence.",
            "TQQQ is a leveraged ETF tracking the Nasdaq-100.",
            "Python is a common tool in data science and AI."
        ]
    })

def hello_tool_func(name):
    return call_mcp_tool("hello_tool", {"name": name})

tools = [
    Tool(
        name="web_crawl_tool",
        func=web_crawl_tool_func,
        description="Searches the web and crawls the top result using FireCrawl."
    ),
    Tool(
        name="embedder_tool",
        func=embedder_tool_func,
        description="Embed text for vector search"
    ),
    Tool(
        name="similarity_search_tool",
        func=similarity_search_tool_func,
        description="Perform semantic search across documents"
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

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

async def run_main():
    print("Simple ReAct Agent for MCP Server (HTTP mode) (type 'exit' to quit)")
    while True:
        user_input = input("\nAsk a question: ")
        if user_input.strip().lower() == "exit":
            break
        response = await agent.ainvoke({"input": user_input})
        print(f"\nAgent Response:\n{response}")

if __name__ == "__main__":
    asyncio.run(run_main())