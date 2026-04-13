#!/usr/bin/env python3
"""Plan-and-Execute + Reflection Research Agent — Demo 4.

Uses the Claude Agent SDK with a structured 3-phase system prompt:
  1. PLAN — decompose topic into 3-5 concrete research steps
  2. EXECUTE — research each step sequentially with per-step evaluation
  3. REFLECT — self-critique the draft and optionally correct (max 1 iteration)

Output includes the research plan, final report, reflection notes, and meta-info.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from utils import (
    DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS,
    PLAN_REFLECT_SYSTEM_PROMPT as SYSTEM_PROMPT,
    check_report_structure, slugify, strip_preamble,
)


async def run_research(topic: str, output_dir: Path) -> None:
    """Run the plan-and-reflect research agent on the given topic."""
    print(f"\n{'='*60}")
    print(f"  Plan & Reflect Research Agent — Demo 4")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=DEFAULT_TOOLS,
        permission_mode=DEFAULT_PERMISSION_MODE,
        max_turns=40,
    )

    report_parts: list[str] = []
    cost_usd = 0.0
    turn_count = 0

    print("Phase 1: Planning research steps...")
    print("Phase 2: Executing research plan...")
    print("Phase 3: Reflecting and self-critiquing...\n")
    print("Agent is working... (this may take a few minutes)\n")

    async for message in query(prompt=f"Research: {topic}", options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    report_parts.append(block.text)
                    # Show progress dots
                    print(".", end="", flush=True)

        elif isinstance(message, ResultMessage):
            cost_usd = getattr(message, "total_cost_usd", 0.0) or 0.0

    print("\n")

    # Combine all text blocks and strip any preamble artifacts
    full_output = strip_preamble("\n".join(report_parts))

    if not full_output.strip():
        print("ERROR: Agent returned empty output.")
        sys.exit(1)

    # Save full output (plan + report + reflection + meta)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"plan-reflect-{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(full_output, encoding="utf-8")

    structure = check_report_structure(full_output)

    print(f"Output saved to:  {output_path}")
    print(f"Report length:    {len(full_output.split())} words")
    print(f"Agent turns:      {turn_count}")
    print(f"Cost:             ${cost_usd:.4f}")
    print(f"\nStructure check:")
    print(f"  Research Plan:  {'✓' if structure['has_plan'] else '✗'}")
    print(f"  Reflection:     {'✓' if structure['has_reflection'] else '✗'}")
    print(f"  Meta-info:      {'✓' if structure['has_meta'] else '✗'}")
    print(f"  Correction:     {'Yes' if structure['correction_triggered'] else 'No'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan & Reflect Research Agent — structured planning + self-critique research."
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

    asyncio.run(run_research(args.topic, Path(args.output_dir)))


if __name__ == "__main__":
    main()
