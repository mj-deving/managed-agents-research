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
import re
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

SYSTEM_PROMPT = """\
You are a research specialist. When given a topic, follow this process:

1. **Decompose** the topic into 3-5 specific subtopics that together cover the subject comprehensively.
2. **Research** each subtopic using WebSearch to find current, authoritative sources. Use WebFetch to read promising pages in detail when needed.
3. **Evaluate** sources for credibility and recency. Prefer official documentation, peer-reviewed papers, reputable news outlets, and expert analyses.
4. **Write** a structured research report in clean Markdown with these sections:
   - **Executive Summary** — 2-3 paragraph overview of key findings
   - **Key Findings** — One subsection per subtopic with detailed analysis
   - **Sources** — Numbered list of all sources with titles and URLs
   - **Conclusions** — Synthesis of findings, trends, and implications

Rules:
- Every factual claim must be backed by a source from your research.
- Include at least 8 sources total.
- Write 1500-2500 words.
- Use clear, professional language.
- Do NOT fabricate or hallucinate URLs.
- Output ONLY the Markdown report, no preamble or commentary.
"""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


async def do_research(topic: str) -> dict:
    """Run research agent and return results dict."""
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=30,
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
    return {
        "topic": topic,
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

    print(f"\n[{time.strftime('%H:%M:%S')}] Research request: {topic}")

    start = time.time()
    result = await do_research(topic)
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
    print(f"  POST /research  — {{\"topic\": \"your topic\"}}")
    print(f"  GET  /health    — health check\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
