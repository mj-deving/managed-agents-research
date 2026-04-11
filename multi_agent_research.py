#!/usr/bin/env python3
"""Multi-Agent Research — Demo 2.

Uses ClaudeSDKClient with AgentDefinition to spawn parallel sub-agents
per subtopic. An orchestrator agent decomposes the topic, delegates research
to specialized sub-agents, and stitches the final report.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TaskNotificationMessage,
    TaskProgressMessage,
    TaskStartedMessage,
    TextBlock,
)

ORCHESTRATOR_PROMPT = """\
You are a research orchestrator. When given a topic:

1. **Decompose** the topic into 3-5 specific, non-overlapping subtopics.
2. **Delegate** each subtopic to a "researcher" agent using the Agent tool. \
Spawn ALL sub-agents — do not research subtopics yourself. \
For each agent call, provide the subtopic as the prompt. Use this format:
   - Agent name: "researcher"
   - Prompt: "Research: [specific subtopic]. Find authoritative sources, \
evaluate them, and write a detailed analysis section (400-600 words) with \
source URLs."
3. **Wait** for all sub-agents to complete and collect their results.
4. **Stitch** the results into a single cohesive report with these sections:
   - **Executive Summary** — 2-3 paragraph synthesis of all findings
   - **Key Findings** — One section per subtopic (from sub-agent results)
   - **Sources** — Consolidated, deduplicated source list with URLs
   - **Conclusions** — Overall synthesis, trends, implications

Rules:
- You MUST use the Agent tool to delegate research. Do NOT research yourself.
- Spawn agents in parallel when possible for speed.
- The final report should be 1500-2500 words.
- Output ONLY the final Markdown report after all agents complete.
"""

RESEARCHER_PROMPT = """\
You are a focused research specialist. When given a subtopic:

1. Use WebSearch to find 3-5 authoritative, current sources.
2. Use WebFetch to read the most promising pages in detail.
3. Evaluate sources for credibility and recency.
4. Write a detailed analysis section (400-600 words) covering:
   - Key facts and data points
   - Current trends and developments
   - Notable quotes or statistics
5. End with a numbered source list with titles and URLs.

Rules:
- Every claim must be backed by a source you found.
- Do NOT fabricate URLs.
- Be thorough but concise.
- Output ONLY the analysis and sources, no preamble.
"""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


async def run_multi_agent_research(topic: str, output_dir: Path) -> None:
    """Run the multi-agent research pipeline."""
    print(f"\n{'='*60}")
    print(f"  Multi-Agent Research — Demo 2")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        system_prompt=ORCHESTRATOR_PROMPT,
        allowed_tools=["WebSearch", "WebFetch", "Read"],
        permission_mode="bypassPermissions",
        max_turns=60,
        agents={
            "researcher": AgentDefinition(
                description="Research specialist that investigates a specific subtopic using web search",
                prompt=RESEARCHER_PROMPT,
                tools=["WebSearch", "WebFetch"],
                model="sonnet",
                maxTurns=20,
                permissionMode="bypassPermissions",
            ),
        },
    )

    tasks: dict[str, dict] = {}
    report_parts: list[str] = []
    cost_usd = 0.0

    print("Orchestrator is decomposing topic and spawning sub-agents...\n")

    async with ClaudeSDKClient(options) as client:
        await client.query(f"Research: {topic}")

        async for message in client.receive_response():
            if isinstance(message, TaskStartedMessage):
                tasks[message.task_id] = {
                    "description": message.description,
                    "status": "running",
                }
                print(f"  [+] Sub-agent started: {message.description}")

            elif isinstance(message, TaskProgressMessage):
                if message.task_id in tasks:
                    tokens = message.usage["total_tokens"] if message.usage else 0
                    print(f"  ... {tasks[message.task_id]['description'][:50]} ({tokens} tokens)", end="\r")

            elif isinstance(message, TaskNotificationMessage):
                if message.task_id in tasks:
                    tasks[message.task_id]["status"] = message.status
                    tasks[message.task_id]["summary"] = message.summary
                    tasks[message.task_id]["output_file"] = message.output_file
                    usage = message.usage
                    tokens = usage["total_tokens"] if usage else 0
                    tasks[message.task_id]["tokens"] = tokens
                    print(f"  [✓] Sub-agent done: {message.summary[:60]}... ({tokens} tokens)")

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        report_parts.append(block.text)

            elif isinstance(message, ResultMessage):
                cost_usd = getattr(message, "total_cost_usd", 0.0) or 0.0

    print()

    # Combine report
    report = "\n".join(report_parts)

    if not report.strip():
        print("ERROR: Orchestrator returned empty report.")
        sys.exit(1)

    # Save report
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"multi-{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(report, encoding="utf-8")

    # Print summary
    print(f"\nReport saved to: {output_path}")
    print(f"Report length:   {len(report.split())} words")
    print(f"Total cost:      ${cost_usd:.4f}")
    print(f"\nSub-agent breakdown:")
    for task_id, info in tasks.items():
        tokens = info.get("tokens", "?")
        print(f"  - {info['description'][:60]}: {info['status']} ({tokens} tokens)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research — orchestrator decomposes topic and spawns parallel sub-agents."
    )
    parser.add_argument("topic", help="The topic to research")
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory to save the report (default: output/)",
    )
    args = parser.parse_args()

    asyncio.run(run_multi_agent_research(args.topic, Path(args.output_dir)))


if __name__ == "__main__":
    main()
