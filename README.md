SearchAI: Multi-Agent Local Search Platform

Overview

SearchAI is a local-first, multi-agent system for advanced search, retrieval, and reasoning. It leverages FastMCP for tool orchestration and LangChain for agentic workflows. The system is designed for privacy, extensibility, and robust local operation—no cloud dependencies required.

Features
	•	Multi-tool agentic reasoning: Agents can use web search, web crawling, semantic search, embedding, and finance tools.
	•	Local-first: All components run on your machine. No cloud APIs required (except for optional LLM/embedding providers).
	•	Extensible: Add new tools as Python functions.
	•	Modular: Clean separation between agent, server, and tools.

Architecture

[User] ⇄ [LangChain Agent] ⇄ [FastMCP Server] ⇄ [Tools]

	•	LangChain Agent: Orchestrates tool use, provides reasoning traces.
	•	FastMCP Server: Exposes tools (web search, crawl, embedding, finance, etc.) via HTTP.
	•	Tools: Python functions for search, embedding, finance, etc.

Setup Instructions

1. Clone the repository

git clone <your-repo-url>
cd SearchAI

2. Install dependencies

We recommend using uv or pip:

uv pip install -r requirements.txt
# or
pip install -r requirements.txt

Or, if using Poetry:

poetry install

3. Set environment variables

Create a .env file in the project root with the following (as needed):

OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
FIRECRAWL_API_KEY=...

	•	Only set the keys for the tools you want to use.
	•	For local-only operation, you can skip cloud keys, but some tools (embedding, hybrid search) require them.

4. Install extra system dependencies (if needed)
	•	uvicorn (for running the server)
	•	yfinance, pinecone-text, etc. (see pyproject.toml)

Running the System

1. Start the FastMCP Server

uvicorn fastmcp_server.server:mcp.run --reload
# or, if using the __main__ block:
python -m fastmcp_server.server

2. Start the Agent (CLI mode)

python main.py

	•	This launches a CLI chatbot that interacts with the MCP server.

Example Usage
	•	Ask questions like:
	•	“What is TQQQ?”
	•	“Get the latest price for AAPL.”
	•	“Summarize the top web result for ‘LangChain’.”
	•	“Embed this text for search: …”
	•	The CLI will show both the agent’s answer and its step-by-step tool usage.

Extending Tools
	•	Add new tools as Python functions in fastmcp_server/server.py using the @mcp.tool decorator.
	•	Restart the server to register new tools.
	•	Update the agent’s tool list in main.py if needed.

Troubleshooting
	•	Server not responding? Ensure the MCP server is running and accessible.
	•	Missing dependencies? Run pip install -r requirements.txt or check pyproject.toml for extras.
	•	API keys missing? Set required keys in your .env file.
	•	Tool errors? Check server logs for stack traces.

License

MIT

⸻

For questions or contributions, open an issue or pull request!