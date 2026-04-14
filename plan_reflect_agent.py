#!/usr/bin/env python3
"""Plan-and-Execute + Reflection Research Agent — Demo 4.

Uses the Claude Agent SDK with 3 separate query() calls, each using the
optimal model for its phase:
  1. PLAN (Haiku)    — decompose topic into 3-5 concrete research steps
  2. EXECUTE (Sonnet) — research each step sequentially with per-step evaluation
  3. REFLECT (Haiku)  — self-critique the draft, flag gaps

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
    DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS, HAIKU_MODEL,
    EXECUTE_PHASE_PROMPT, PLAN_PHASE_PROMPT, REFLECT_PHASE_PROMPT,
    check_report_structure, slugify, strip_preamble,
)


async def run_phase(prompt: str, system_prompt: str, model: str,
                    max_turns: int, tools: list[str] | None = None) -> tuple[str, float, int]:
    """Run a single agent phase and return (text, cost, turns)."""
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        allowed_tools=tools or [],
        permission_mode=DEFAULT_PERMISSION_MODE,
        max_turns=max_turns,
    )

    parts: list[str] = []
    cost_usd = 0.0
    turn_count = 0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
                    print(".", end="", flush=True)
        elif isinstance(message, ResultMessage):
            cost_usd = getattr(message, "total_cost_usd", 0.0) or 0.0

    return "\n".join(parts), cost_usd, turn_count


async def run_research(topic: str, output_dir: Path) -> None:
    """Run the 3-phase plan-and-reflect research agent."""
    print(f"\n{'='*60}")
    print(f"  Plan & Reflect Research Agent — Demo 4")
    print(f"  Topic: {topic}")
    print(f"  Models: Plan=Haiku, Execute=Sonnet, Reflect=Haiku")
    print(f"{'='*60}\n")

    total_cost = 0.0
    total_turns = 0

    # --- Phase 1: Plan (Haiku) ---
    print(f"Phase 1: Planning research steps (Haiku)...")
    plan_text, plan_cost, plan_turns = await run_phase(
        prompt=f"Create a research plan for: {topic}",
        system_prompt=PLAN_PHASE_PROMPT,
        model=HAIKU_MODEL,
        max_turns=5,
    )
    plan_text = strip_preamble(plan_text)
    total_cost += plan_cost
    total_turns += plan_turns
    print(f" done ({plan_turns} turns, ${plan_cost:.4f})\n")

    if not plan_text.strip():
        print("ERROR: Plan phase returned empty output.")
        sys.exit(1)

    # --- Phase 2: Execute (Sonnet) ---
    print(f"Phase 2: Executing research plan (Sonnet)...")
    execute_prompt = f"""Here is the research plan to execute:

{plan_text}

Now execute this plan. Research the topic: {topic}"""

    report_text, exec_cost, exec_turns = await run_phase(
        prompt=execute_prompt,
        system_prompt=EXECUTE_PHASE_PROMPT,
        model=DEFAULT_MODEL,
        max_turns=30,
        tools=DEFAULT_TOOLS,
    )
    report_text = strip_preamble(report_text)
    total_cost += exec_cost
    total_turns += exec_turns
    print(f" done ({exec_turns} turns, ${exec_cost:.4f})\n")

    if not report_text.strip():
        print("ERROR: Execute phase returned empty output.")
        sys.exit(1)

    # --- Phase 3: Reflect (Haiku) ---
    print(f"Phase 3: Reflecting and self-critiquing (Haiku)...")
    reflect_prompt = f"""Evaluate this research output:

PLAN:
{plan_text}

REPORT:
{report_text}"""

    reflect_text, reflect_cost, reflect_turns = await run_phase(
        prompt=reflect_prompt,
        system_prompt=REFLECT_PHASE_PROMPT,
        model=HAIKU_MODEL,
        max_turns=5,
    )
    reflect_text = strip_preamble(reflect_text)
    total_cost += reflect_cost
    total_turns += reflect_turns
    print(f" done ({reflect_turns} turns, ${reflect_cost:.4f})\n")

    # --- Combine output ---
    full_output = f"{plan_text}\n\n{report_text}\n\n{reflect_text}"

    # Save full output
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"plan-reflect-{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(full_output, encoding="utf-8")

    structure = check_report_structure(full_output)

    print(f"Output saved to:  {output_path}")
    print(f"Report length:    {len(full_output.split())} words")
    print(f"Total turns:      {total_turns} (plan={plan_turns}, exec={exec_turns}, reflect={reflect_turns})")
    print(f"Total cost:       ${total_cost:.4f} (plan=${plan_cost:.4f}, exec=${exec_cost:.4f}, reflect=${reflect_cost:.4f})")
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
