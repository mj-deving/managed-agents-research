#!/usr/bin/env python3
"""Multi-Agent Research — Demo 2.

Uses ClaudeSDKClient with AgentDefinition to spawn parallel sub-agents
per subtopic. An orchestrator agent decomposes the topic, delegates research
to specialized sub-agents, and stitches the final report.
"""

import argparse
import asyncio
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

from utils import DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS, RESEARCHER_PROMPT, slugify

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

async def run_multi_agent_research(topic: str, output_dir: Path) -> None:
    """Run the multi-agent research pipeline."""
    print(f"\n{'='*60}")
    print(f"  Multi-Agent Research — Demo 2")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=ORCHESTRATOR_PROMPT,
        allowed_tools=DEFAULT_TOOLS + ["Read"],
        permission_mode=DEFAULT_PERMISSION_MODE,
        max_turns=60,
        agents={
            "researcher": AgentDefinition(
                description="Research specialist that investigates a specific subtopic using web search",
                prompt=RESEARCHER_PROMPT,
                tools=DEFAULT_TOOLS,
                model="sonnet",
                maxTurns=20,
                permissionMode=DEFAULT_PERMISSION_MODE,
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
