#!/usr/bin/env python3
"""Multi-Agent Plan & Reflect Research — Demo 5.

Combines multi-agent orchestration (Demo 2) with Plan-and-Execute + Reflection
(Demo 4). The orchestrator plans research steps, delegates each step to a
sub-agent, then reflects on the combined results.

Uses ClaudeSDKClient with AgentDefinition for parallel sub-agent execution.
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

from utils import (
    DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS, RESEARCHER_PROMPT,
    check_report_structure, slugify, strip_preamble,
)

ORCHESTRATOR_PROMPT = """\
You are a research orchestrator using a structured Plan-and-Execute methodology \
with self-reflection. Follow these three phases EXACTLY in order.

━━━ PHASE 1: PLAN ━━━

Before delegating any research, create a concrete research plan.

1. Analyze the topic and identify 3-5 specific research questions.
2. For each question, note what kind of source would best answer it.
3. Output the plan in this EXACT format:

## Research Plan

| Step | Research Question | Target Source Type |
|------|------------------|--------------------|
| 1 | [specific question] | [e.g., official docs, news, academic] |
| 2 | [specific question] | [source type] |
| ... | ... | ... |

━━━ PHASE 2: DELEGATE ━━━

For EACH step in the plan, spawn a "researcher" sub-agent using the Agent tool:
- Agent name: "researcher"
- Prompt: "Research: [the specific research question from that step]. \
Find 3-5 authoritative sources, evaluate them, and write a detailed analysis \
section (400-600 words) with source URLs."

Spawn ALL sub-agents — do NOT research any step yourself.
Wait for all sub-agents to complete.

━━━ PHASE 3: SYNTHESIZE + REFLECT ━━━

After all sub-agents return results:

1. **Stitch** the results into a cohesive report:

## Report

- **Executive Summary** — 2-3 paragraph synthesis of all findings
- **Key Findings** — One section per research question (from sub-agent results)
- **Sources** — Consolidated, deduplicated source list with URLs
- **Conclusions** — Overall synthesis, trends, implications

2. **Reflect** on the combined output:

## Reflection Notes

1. **Plan Coverage**: For each step in the plan, was it adequately addressed?
2. **Source Quality**: Are sources authoritative and current?
3. **Contradictions**: Are there conflicting findings? How were they resolved?
4. **Overall Assessment**: Rate the report (Strong / Adequate / Needs Improvement).

If "Needs Improvement": do targeted follow-up research yourself (max 2 searches) \
and update the relevant sections. Note what was corrected.

3. **Meta-info** — end with:

## Meta

- **Research steps planned**: [number]
- **Research steps delegated**: [number of sub-agents spawned]
- **Reflection triggered correction**: [Yes/No]
- **Correction details**: [what was fixed, or "N/A"]

Rules:
- You MUST use the Agent tool to delegate research. Do NOT research yourself.
- The final report should be 1500-2500 words.
- Output ONLY the plan, report, reflection, and meta sections.
"""

async def run_plan_reflect_multi_agent(topic: str, output_dir: Path) -> None:
    """Run the multi-agent plan-and-reflect research pipeline."""
    print(f"\n{'='*60}")
    print(f"  Multi-Agent Plan & Reflect Research — Demo 5")
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
                description="Research specialist that investigates a specific research question using web search",
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

    print("Phase 1: Planning research steps...")
    print("Phase 2: Delegating to sub-agents...")
    print("Phase 3: Synthesizing + reflecting...\n")

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

    # Combine and clean output
    full_output = strip_preamble("\n".join(report_parts))

    if not full_output.strip():
        print("ERROR: Orchestrator returned empty output.")
        sys.exit(1)

    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"plan-reflect-multi-{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(full_output, encoding="utf-8")

    structure = check_report_structure(full_output)

    print(f"\nOutput saved to:  {output_path}")
    print(f"Report length:    {len(full_output.split())} words")
    print(f"Total cost:       ${cost_usd:.4f}")
    print(f"\nStructure check:")
    print(f"  Research Plan:  {'✓' if structure['has_plan'] else '✗'}")
    print(f"  Reflection:     {'✓' if structure['has_reflection'] else '✗'}")
    print(f"  Meta-info:      {'✓' if structure['has_meta'] else '✗'}")
    print(f"  Correction:     {'Yes' if structure['correction_triggered'] else 'No'}")
    print(f"\nSub-agent breakdown:")
    for task_id, info in tasks.items():
        tokens = info.get("tokens", "?")
        print(f"  - {info['description'][:60]}: {info['status']} ({tokens} tokens)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Plan & Reflect Research — orchestrator plans, delegates, and reflects."
    )
    parser.add_argument(
        "topic",
        help="The topic to research (e.g., 'State of AI Coding Agents 2026')",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory to save the output (default: output/)",
    )
    args = parser.parse_args()

    asyncio.run(run_plan_reflect_multi_agent(args.topic, Path(args.output_dir)))


if __name__ == "__main__":
    main()
