#!/usr/bin/env python3
"""Simple Research Agent — Demo 1.

Uses the Claude Agent SDK to research a topic autonomously and produce
a structured Markdown report with real web sources.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

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
3. **Evaluate** sources for credibility and recency. Prefer official documentation, peer-reviewed papers, reputable news outlets, and expert analyses. Discard low-quality or outdated sources.
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
- Do NOT fabricate or hallucinate URLs — only include sources you actually found via search.
- Output ONLY the Markdown report, no preamble or commentary.
"""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


async def run_research(topic: str, output_dir: Path) -> None:
    """Run the research agent on the given topic."""
    print(f"\n{'='*60}")
    print(f"  Research Agent — Demo 1")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

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

    print("Agent is researching... (this may take a few minutes)\n")

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

    # Combine all text blocks into the final report
    report = "\n".join(report_parts)

    if not report.strip():
        print("ERROR: Agent returned empty report.")
        sys.exit(1)

    # Save report
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(report, encoding="utf-8")

    print(f"Report saved to: {output_path}")
    print(f"Report length:   {len(report.split())} words")
    print(f"Agent turns:     {turn_count}")
    print(f"Cost:            ${cost_usd:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research Agent — autonomously researches a topic and produces a Markdown report."
    )
    parser.add_argument("topic", help="The topic to research (e.g., 'State of AI Coding Agents 2026')")
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory to save the report (default: output/)",
    )
    args = parser.parse_args()

    asyncio.run(run_research(args.topic, Path(args.output_dir)))


if __name__ == "__main__":
    main()
