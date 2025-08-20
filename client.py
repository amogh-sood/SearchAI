#!/usr/bin/env python3
"""
Minimal ACP-only client.

- Talks ONLY to the ACP server (no MCP usage here).
- Auto-discovers agents and auto-selects a default (agent → chat_agent → echo → first).
- Supports explicit --agent-name to target a specific ACP agent.
- Handles both schemas: {"agent": "..."} and {"agent_name": "..."} on /runs.
"""

import asyncio
import argparse
import json
import os
import httpx
from typing import List, Optional

from acp_sdk.client import Client as ACPClient
from acp_sdk.models import Message, MessagePart
try:
    from acp_sdk.models.errors import ACPError  # type: ignore
except Exception:
    ACPError = Exception  # type: ignore

# Normalize heterogeneous ACP outputs (strings, dicts with content, Message-like objects)
def _normalize_output(seq):
    out = []
    for item in (seq or []):
        # already a string
        if isinstance(item, str):
            out.append(item)
            continue
        # server might return dicts like {"content": ...}
        if isinstance(item, dict) and "content" in item:
            out.append(str(item["content"]))
            continue
        # Message-like object with .content attribute
        content = getattr(item, "content", None)
        if content is not None:
            out.append(str(content))
            continue
        # Fallback stringification
        out.append(str(item))
    return out

# If your ACP API is mounted under a prefix, include it here (or via --acp-url)
# e.g. http://localhost:8002/acp
ACP_SERVER_URL = os.getenv("ACP_URL", "http://127.0.0.1:8002")


async def discover_agents(base_url: str) -> List[str]:
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as http:
            r = await http.get("/agents")
            r.raise_for_status()
            data = r.json()
            names: List[str] = []
            # Support {"agents":[{"name":"..."}]} or {"agents":["...", "..."]}
            for item in data.get("agents", []):
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    names.append(item["name"])
                elif isinstance(item, str):
                    names.append(item)
            return names
    except Exception:
        return []


async def choose_default_agent(base_url: str) -> Optional[str]:
    names = await discover_agents(base_url)
    for preferred in ("agent", "chat_agent", "echo"):
        if preferred in names:
            return preferred
    return names[0] if names else None


async def run_with_fallback(base_url: str, agent_name: str, text: Optional[str]):
    """Try SDK run (agent=...), fall back to raw POST with agent_name if needed."""
    parts = [] if text is None else [MessagePart(content=text)]
    async with ACPClient(base_url=base_url) as client:
        try:
            run = await client.run_sync(agent=agent_name, input=[Message(parts=parts)])
            return list(run.output)
        except ACPError:
            # Fallback: server expects {"agent_name": ...}
            async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as http:
                r = await http.post(
                    "/runs",
                    headers={"Content-Type": "application/json"},
                    json={
                        "agent_name": agent_name,
                        "input": [] if text is None else [{"parts": [{"content": text}]}],
                    },
                )
                r.raise_for_status()
                data = r.json()
                out = data.get("output") or data.get("data") or []
                if isinstance(out, str):
                    out = [out]
                return out


async def ask_anything(base_url: str, text: str) -> None:
    name = await choose_default_agent(base_url)
    if not name:
        print("No agents found at:", base_url)
        print("Tip: ensure your ACP server is running and the URL (and prefix) is correct.")
        return
    out = await run_with_fallback(base_url, name, text)
    out = _normalize_output(out)
    print(f"{name} says:", "".join(out))


async def call_named(base_url: str, agent_name: str, text: Optional[str]) -> None:
    names = await discover_agents(base_url)
    if agent_name not in names:
        print(f"Agent '{agent_name}' not found at {base_url}. Available: {', '.join(names) or '<none>'}")
        return
    out = await run_with_fallback(base_url, agent_name, text)
    out = _normalize_output(out)
    label = text if text is not None else "(no input)"
    print(f"{agent_name}({label}) →", "".join(out))


async def main() -> None:
    parser = argparse.ArgumentParser(description="ACP-only client")
    parser.add_argument("--acp-url", default=None, help="ACP base URL (e.g., http://127.0.0.1:8002 or .../acp)")
    parser.add_argument("--agent-name", default=None, help="Explicit ACP agent name to call (e.g., stockAgent)")
    parser.add_argument("--date", action="store_true", help="Call 'dateAgent' (no input).")
    parser.add_argument("--agent", metavar="MESSAGE", help="Send message to default 'agent' (shortcut).")
    parser.add_argument("message", nargs="?", help="If provided alone, auto-pick an agent and send this message.")
    args = parser.parse_args()

    base = args.acp_url or ACP_SERVER_URL

    if args.date:
        await call_named(base, "dateAgent", None)
    elif args.agent is not None and args.agent_name is None:
        await call_named(base, "agent", args.agent)
    elif args.agent_name:
        # If positional message is given, use it as input; else None
        text = args.message if args.message is not None else args.agent
        await call_named(base, args.agent_name, text)
    elif args.message:
        await ask_anything(base, args.message)
    else:
        # simple interactive mode
        print("ACP interactive mode (q to quit).")
        while True:
            choice = input("1) ask-anything  2) dateAgent  3) named agent  q) quit: ").strip().lower()
            if choice == "1":
                msg = input("message: ")
                await ask_anything(base, msg)
            elif choice == "2":
                await call_named(base, "dateAgent", None)
            elif choice == "3":
                name = input("agent name: ").strip()
                msg = input("message (empty for none): ").strip()
                await call_named(base, name, msg if msg else None)
            elif choice.startswith("q"):
                print("bye")
                break
            else:
                print("invalid; try again")


if __name__ == "__main__":
    asyncio.run(main())