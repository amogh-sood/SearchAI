# SearchAI: Multi-Agent Python CLI

## Overview
SearchAI is a multi-agent system for advanced search, retrieval, and reasoning. It uses FastMCP for tool orchestration and LangChain for agentic workflows. The system runs on your machine, but some features require cloud APIs (such as OpenAI, Pinecone, and FireCrawl) for embedding, hybrid search, and web crawling.

## Features (Current)
- **FastMCP server** exposing the following tools:
  - Web search and crawl (DuckDuckGo + FireCrawl, requires FireCrawl API key)
  - Yahoo Finance price lookup
  - Text embedding (OpenAI/Pinecone, requires OpenAI and Pinecone API keys)
  - Hybrid similarity search (semantic + keyword, requires OpenAI and Pinecone API keys)
  - Hello tool (demo)
- **LangChain CLI agent** that can:
  - Use all registered MCP tools
  - Answer questions and show results in the terminal
- **HTTP communication** between agent and server
- **Extensible**: Add new tools as Python functions

## File Structure & Purpose

```
SearchAI/
├── fastmcp_server/
│   └── server.py         # FastMCP server and tool definitions
├── main.py               # CLI agent that interacts with the MCP server
├── pyproject.toml        # Python dependencies
├── uv.lock               # Lockfile for uv/pip
├── README.md             # This file
```

### Key Files
- **fastmcp_server/server.py**: Implements the FastMCP server and all available tools. Tools include web crawling, Yahoo Finance, embedding, similarity search, and a hello tool.
- **main.py**: CLI chatbot agent. Connects to the MCP server via HTTP, exposes all tools, and allows interactive Q&A in the terminal.
- **pyproject.toml**: Lists all Python dependencies (FastMCP, LangChain, yfinance, etc).
- **uv.lock**: Lockfile for reproducible installs.

## Setup Instructions

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd SearchAI
```

### 2. Install dependencies
We recommend using [uv](https://github.com/astral-sh/uv) or pip:
```sh
uv pip install -r requirements.txt
# or
pip install -r requirements.txt
```
Or, if using Poetry:
```sh
poetry install
```

### 3. Set environment variables
Create a `.env` file in the project root with the following (as needed):
```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
FIRECRAWL_API_KEY=...
```
- Set the keys for the tools you want to use.
- Embedding and hybrid search require OpenAI and Pinecone API keys.
- Web crawling requires a FireCrawl API key.

## Usage

### 1. Start the FastMCP Server
```sh
python -m fastmcp_server.server
```
- This will start the server on `http://localhost:8000/mcp/` by default.

### 2. Start the CLI Agent
```sh
python main.py
```
- This launches a CLI chatbot that interacts with the MCP server.
- Type your questions and see the agent's answers in the terminal.
- Type `exit` to quit.

## Example Usage
- "What is TQQQ?"
- "Get the latest price for AAPL."
- "Summarize the top web result for 'LangChain'."
- "Embed this text for search: ..."

## Adding New Tools
- Add new tools as Python functions in `fastmcp_server/server.py` using the `@mcp.tool` decorator.
- Restart the server to register new tools.
- Update the agent’s tool list in `main.py` if needed.

## Troubleshooting
- **Server not responding?** Ensure the MCP server is running and accessible at the URL set in the agent.
- **Missing dependencies?** Run `pip install -r requirements.txt` or check `pyproject.toml` for extras.
- **API keys missing?** Set required keys in your `.env` file for the features you want to use.
- **Tool errors?** Check server logs for stack traces.

## License
MIT