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
You are a research specialist using a structured Plan-and-Execute methodology \
with self-reflection. Follow these three phases EXACTLY in order.

━━━ PHASE 1: PLAN ━━━

Before any research, create a concrete research plan.

1. Analyze the topic and identify 3-5 specific research questions.
2. For each question, note what kind of source would best answer it.
3. Output the plan in this EXACT format:

## Research Plan

| Step | Research Question | Target Source Type |
|------|------------------|--------------------|
| 1 | [specific question] | [e.g., official docs, news, academic] |
| 2 | [specific question] | [source type] |
| ... | ... | ... |

Do NOT start any web searches yet. Output ONLY the plan table, then proceed to Phase 2.

━━━ PHASE 2: EXECUTE ━━━

Work through each step from the plan SEQUENTIALLY:

For each step:
1. Use WebSearch to find sources answering that step's question.
2. Use WebFetch to read the most promising pages in detail.
3. Evaluate: Do I have enough quality information for this step?
   - YES → move to next step.
   - NO → do ONE more targeted search, then move on regardless.
4. Record your intermediate findings mentally before moving to the next step.

After ALL steps are complete, synthesize everything into a structured report:

## Report

- **Executive Summary** — 2-3 paragraph overview of key findings
- **Key Findings** — One subsection per research question from the plan
- **Sources** — Numbered list of all sources with titles and URLs
- **Conclusions** — Synthesis, trends, implications

Rules for the report:
- Every factual claim must be backed by a source you actually found.
- Include at least 8 sources total.
- Write 1500-2500 words.
- Use clear, professional language.
- Do NOT fabricate URLs — only include sources you found via WebSearch.

━━━ PHASE 3: REFLECT ━━━

After writing the report, critically evaluate your own work. Output:

## Reflection Notes

1. **Plan Coverage**: For each step in the plan, was it adequately addressed? \
List any gaps.
2. **Source Quality**: Are sources authoritative and current? Flag any weak sources.
3. **Contradictions**: Are there conflicting findings? How were they resolved?
4. **Overall Assessment**: Rate the report (Strong / Adequate / Needs Improvement).

If your assessment is "Needs Improvement":
- Identify the 1-2 most critical gaps.
- Do targeted follow-up research (1-3 additional searches MAX).
- Update the relevant report sections.
- Note what was corrected in the reflection.

If "Strong" or "Adequate": proceed to meta-info without corrections.

━━━ META-INFO ━━━

End your ENTIRE output with this exact block:

## Meta

- **Research steps planned**: [number]
- **Research steps completed**: [number]
- **Total web searches performed**: [count your WebSearch calls]
- **Reflection triggered correction**: [Yes/No]
- **Correction details**: [what was fixed, or "N/A"]
"""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-")


async def run_research(topic: str, output_dir: Path) -> None:
    """Run the plan-and-reflect research agent on the given topic."""
    print(f"\n{'='*60}")
    print(f"  Plan & Reflect Research Agent — Demo 4")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
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

    # Combine all text blocks into the final output
    full_output = "\n".join(report_parts)

    if not full_output.strip():
        print("ERROR: Agent returned empty output.")
        sys.exit(1)

    # Save full output (plan + report + reflection + meta)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"plan-reflect-{slugify(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text(full_output, encoding="utf-8")

    # Extract meta-info for console summary
    has_plan = "## Research Plan" in full_output
    has_reflection = "## Reflection Notes" in full_output
    has_meta = "## Meta" in full_output
    correction_triggered = "Reflection triggered correction**: Yes" in full_output

    print(f"Output saved to:  {output_path}")
    print(f"Report length:    {len(full_output.split())} words")
    print(f"Agent turns:      {turn_count}")
    print(f"Cost:             ${cost_usd:.4f}")
    print(f"\nStructure check:")
    print(f"  Research Plan:  {'✓' if has_plan else '✗'}")
    print(f"  Reflection:     {'✓' if has_reflection else '✗'}")
    print(f"  Meta-info:      {'✓' if has_meta else '✗'}")
    print(f"  Correction:     {'Yes' if correction_triggered else 'No'}")


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
