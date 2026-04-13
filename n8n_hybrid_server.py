#!/usr/bin/env python3
"""n8n Hybrid Server — Demo 3.

Lightweight HTTP API that n8n (or any HTTP client) can call to trigger
autonomous research. Exposes POST /research endpoint that runs the
research agent and returns the report as JSON.

Usage:
    python3 n8n_hybrid_server.py              # Start on port 8000
    python3 n8n_hybrid_server.py --port 9000  # Custom port

Test with curl:
    curl -X POST http://localhost:8000/research \\
         -H "Content-Type: application/json" \\
         -d '{"topic": "AI Coding Agents 2026"}'
"""

import argparse
import asyncio
import json
import time

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from utils import (
    BASIC_SYSTEM_PROMPT, DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS,
    PLAN_REFLECT_SYSTEM_PROMPT, slugify, strip_preamble,
)


PROMPTS = {
    "basic": (BASIC_SYSTEM_PROMPT, 30),
    "plan-reflect": (PLAN_REFLECT_SYSTEM_PROMPT, 40),
}


async def do_research(topic: str, mode: str = "basic") -> dict:
    """Run research agent and return results dict."""
    system_prompt, max_turns = PROMPTS.get(mode, PROMPTS["basic"])

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        allowed_tools=DEFAULT_TOOLS,
        permission_mode=DEFAULT_PERMISSION_MODE,
        max_turns=max_turns,
    )

    report_parts: list[str] = []
    cost_usd = 0.0
    turn_count = 0

    async for message in query(prompt=f"Research: {topic}", options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    report_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            cost_usd = getattr(message, "total_cost_usd", 0.0) or 0.0

    report = "\n".join(report_parts)
    if mode == "plan-reflect":
        report = strip_preamble(report)

    return {
        "topic": topic,
        "mode": mode,
        "report": report,
        "words": len(report.split()),
        "turns": turn_count,
        "cost_usd": round(cost_usd, 4),
    }


async def research_endpoint(request: Request) -> JSONResponse:
    """POST /research — trigger autonomous research on a topic."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            {"error": "Invalid JSON body"},
            status_code=400,
        )

    topic = body.get("topic")
    if not topic or not isinstance(topic, str):
        return JSONResponse(
            {"error": "Missing or invalid 'topic' field (must be a non-empty string)"},
            status_code=400,
        )

    mode = body.get("mode", "basic")
    if mode not in PROMPTS:
        return JSONResponse(
            {"error": f"Invalid 'mode': must be one of {list(PROMPTS.keys())}"},
            status_code=400,
        )

    print(f"\n[{time.strftime('%H:%M:%S')}] Research request ({mode}): {topic}")

    start = time.time()
    result = await do_research(topic, mode=mode)
    elapsed = time.time() - start
    result["elapsed_seconds"] = round(elapsed, 1)

    print(f"[{time.strftime('%H:%M:%S')}] Done: {result['words']} words, ${result['cost_usd']}, {elapsed:.0f}s")

    return JSONResponse(result)


async def health_endpoint(request: Request) -> JSONResponse:
    """GET /health — simple health check."""
    return JSONResponse({"status": "ok", "service": "research-agent"})


app = Starlette(
    routes=[
        Route("/research", research_endpoint, methods=["POST"]),
        Route("/health", health_endpoint, methods=["GET"]),
    ],
)


def main() -> None:
    parser = argparse.ArgumentParser(description="n8n Hybrid Server — HTTP API for research agent")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    print(f"\nResearch Agent API starting on http://{args.host}:{args.port}")
    print(f"  POST /research  — {{\"topic\": \"...\", \"mode\": \"basic|plan-reflect\"}}")
    print(f"  GET  /health    — health check\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
