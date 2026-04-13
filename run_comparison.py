#!/usr/bin/env python3
"""Comparison Runner — runs Demo 1 (basic) and Demo 4 (plan+reflect) on the
same topic and prints a side-by-side comparison table.

Usage:
    python3 run_comparison.py "State of AI Coding Agents 2026"
    python3 run_comparison.py "RAG Architekturen 2026" -o reports/
"""

import argparse
import asyncio
import time
from pathlib import Path

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


async def run_single(topic: str, system_prompt: str, max_turns: int, label: str) -> dict:
    """Run a single research agent and return metrics."""
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

    start = time.time()

    async for message in query(prompt=f"Research: {topic}", options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    report_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            cost_usd = getattr(message, "total_cost_usd", 0.0) or 0.0

    elapsed = time.time() - start
    report = "\n".join(report_parts)
    if label == "plan-reflect":
        report = strip_preamble(report)

    return {
        "label": label,
        "report": report,
        "words": len(report.split()),
        "turns": turn_count,
        "cost_usd": round(cost_usd, 4),
        "elapsed": round(elapsed, 1),
        "has_plan": "## Research Plan" in report,
        "has_reflection": "## Reflection Notes" in report,
        "has_meta": "## Meta" in report,
    }


async def run_comparison(topic: str, output_dir: Path) -> None:
    """Run Demo 1 and Demo 4 on the same topic and compare."""
    print(f"\n{'='*60}")
    print(f"  Comparison Runner: Demo 1 (basic) vs Demo 4 (plan+reflect)")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    # Run sequentially to avoid API rate limits
    print("Running Demo 1 (basic)...")
    basic = await run_single(topic, BASIC_SYSTEM_PROMPT, 30, "basic")
    print(f"  Done: {basic['words']} words, {basic['turns']} turns, ${basic['cost_usd']}, {basic['elapsed']}s\n")

    print("Running Demo 4 (plan+reflect)...")
    plan_reflect = await run_single(topic, PLAN_REFLECT_SYSTEM_PROMPT, 40, "plan-reflect")
    print(f"  Done: {plan_reflect['words']} words, {plan_reflect['turns']} turns, ${plan_reflect['cost_usd']}, {plan_reflect['elapsed']}s\n")

    # Save both reports
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic)

    basic_path = output_dir / f"compare-basic-{slug}.md"
    basic_path.write_text(basic["report"], encoding="utf-8")

    pr_path = output_dir / f"compare-plan-reflect-{slug}.md"
    pr_path.write_text(plan_reflect["report"], encoding="utf-8")

    # Print comparison table
    print(f"{'='*60}")
    print(f"  COMPARISON RESULTS")
    print(f"{'='*60}\n")

    print(f"{'Metric':<30} {'Demo 1 (basic)':>18} {'Demo 4 (plan+reflect)':>22}")
    print(f"{'-'*70}")
    print(f"{'Words':<30} {basic['words']:>18,} {plan_reflect['words']:>22,}")
    print(f"{'Turns':<30} {basic['turns']:>18} {plan_reflect['turns']:>22}")
    print(f"{'Cost (USD)':<30} {'$'+str(basic['cost_usd']):>18} {'$'+str(plan_reflect['cost_usd']):>22}")
    print(f"{'Runtime (seconds)':<30} {basic['elapsed']:>18} {plan_reflect['elapsed']:>22}")
    print(f"{'Has Research Plan':<30} {str(basic['has_plan']):>18} {str(plan_reflect['has_plan']):>22}")
    print(f"{'Has Reflection':<30} {str(basic['has_reflection']):>18} {str(plan_reflect['has_reflection']):>22}")
    print(f"{'Has Meta-info':<30} {str(basic['has_meta']):>18} {str(plan_reflect['has_meta']):>22}")

    print(f"\nReports saved to:")
    print(f"  Basic:         {basic_path}")
    print(f"  Plan+Reflect:  {pr_path}")

    total_cost = basic["cost_usd"] + plan_reflect["cost_usd"]
    print(f"\nTotal comparison cost: ${total_cost:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comparison Runner — Demo 1 (basic) vs Demo 4 (plan+reflect) on the same topic."
    )
    parser.add_argument(
        "topic",
        help="The topic to research and compare",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory to save reports (default: output/)",
    )
    args = parser.parse_args()

    asyncio.run(run_comparison(args.topic, Path(args.output_dir)))


if __name__ == "__main__":
    main()
