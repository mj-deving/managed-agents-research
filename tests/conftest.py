"""Shared fixtures for the managed-agent-poc test suite."""

import pytest


@pytest.fixture
def sample_basic_report():
    """A realistic Demo 1 basic research report."""
    return """\
# State of AI Coding Agents 2026

## Executive Summary

AI coding agents have evolved significantly in 2026. The market has consolidated
around several key players including GitHub Copilot, Cursor, and Claude Code.
Enterprise adoption continues to grow despite challenges.

## Key Findings

### Leading Platforms

GitHub Copilot crossed 20 million users in 2025. Cursor maintains $500M+ ARR.
Claude Code is preferred for complex architectural tasks.

### Enterprise Adoption

51% of professional developers use AI coding tools daily. However, only 29% of
enterprises report significant ROI from AI coding tools.

## Sources

1. [AI Coding Agents 2026 — Codegen Blog](https://codegen.com/blog/best-ai-coding-agents/)
2. [Coding Agents Comparison — Artificial Analysis](https://artificialanalysis.ai/agents/coding)
3. [AI Coding Statistics — Panto](https://www.getpanto.ai/blog/ai-coding-assistant-statistics)
4. [Enterprise AI Adoption — Writer](https://writer.com/blog/enterprise-ai-adoption-2026/)
5. [Agentic AI Stats — OneReach](https://onereach.ai/blog/agentic-ai-adoption-rates-roi-market-trends/)
6. [SWE-bench Leaderboard — BenchLM](https://benchlm.ai/coding)
7. [AI Coding Benchmarks — Morph LLM](https://www.morphllm.com/ai-coding-benchmarks-2026)
8. [AI Safety Report 2026 — Inside Privacy](https://www.insideprivacy.com/artificial-intelligence/)

## Conclusions

The AI coding agent landscape is maturing rapidly. Individual productivity gains
are well-documented, but organizational ROI remains conditional on workflow redesign.
"""


@pytest.fixture
def sample_plan_reflect_report():
    """A realistic Demo 4 plan-and-reflect report."""
    return """\
## Research Plan

| Step | Research Question | Target Source Type |
|------|------------------|--------------------|
| 1 | What are the leading AI coding agents in 2026? | News, official docs |
| 2 | How do they compare on code generation quality? | Benchmarks, papers |
| 3 | What enterprise adoption patterns are emerging? | Industry reports |

## Report

### Executive Summary

AI coding agents have evolved significantly. The market features several tiers
of tools from IDE extensions to fully autonomous agents.

### Key Findings

#### Step 1: Leading AI Coding Agents

GitHub Copilot leads with 20M+ users. Cursor has $500M+ ARR.

#### Step 2: Code Generation Quality

SWE-bench Verified scores show rapid improvement. Claude Mythos Preview leads at 93.9%.

#### Step 3: Enterprise Adoption

51% of developers use AI daily. Enterprise ROI is conditional on process changes.

### Sources

1. [Codegen Blog](https://codegen.com/blog/best-ai-coding-agents/)
2. [Artificial Analysis](https://artificialanalysis.ai/agents/coding)
3. [Fungies.io](https://fungies.io/best-ai-coding-agents-2026/)
4. [Faros.ai Blog](https://www.faros.ai/blog/best-ai-coding-agents-2026)
5. [Faros.ai Research](https://www.faros.ai/blog/ai-software-engineering)
6. [BenchLM.ai](https://benchlm.ai/coding)
7. [Morph LLM](https://www.morphllm.com/ai-coding-benchmarks-2026)
8. [Inside Privacy](https://www.insideprivacy.com/artificial-intelligence/)

### Conclusions

The paradigm shift is structural, not incremental. Security governance is critical.

## Reflection Notes

1. **Plan Coverage**: All 3 steps adequately addressed.
2. **Source Quality**: 8 sources, mostly authoritative. All current (2026).
3. **Contradictions**: Individual vs enterprise productivity data tensions — addressed in report.
4. **Overall Assessment**: Strong

## Meta

- **Research steps planned**: 3
- **Research steps completed**: 3
- **Total web searches performed**: 6
- **Reflection triggered correction**: No
- **Correction details**: N/A
"""


@pytest.fixture
def sample_plan_reflect_with_correction():
    """A plan-reflect report where reflection triggered a correction."""
    return """\
## Research Plan

| Step | Research Question | Target Source Type |
|------|------------------|--------------------|
| 1 | What is RAG? | Academic papers |
| 2 | How does Graph RAG differ? | Technical docs |

## Report

### Executive Summary

RAG architectures have evolved beyond naive retrieval.

### Key Findings

#### Naive RAG vs Graph RAG

Graph RAG adds knowledge graph structure to retrieval.

### Sources

1. [RAG Overview](https://example.com/rag)
2. [Graph RAG Paper](https://example.com/graph-rag)
3. [Wiki RAG](https://example.com/wiki-rag)
4. [RAG Benchmark](https://example.com/benchmark)
5. [Enterprise RAG](https://example.com/enterprise)
6. [RAG Tutorial](https://example.com/tutorial)
7. [RAG Comparison](https://example.com/comparison)
8. [RAG 2026](https://example.com/rag-2026)

### Conclusions

Graph RAG shows promise for complex domains.

## Reflection Notes

1. **Plan Coverage**: Step 2 lacked depth on implementation details.
2. **Source Quality**: Mixed — 2 sources are blog posts without data.
3. **Contradictions**: None found.
4. **Overall Assessment**: Needs Improvement

Corrected: Added implementation details for Graph RAG from follow-up search.

## Meta

- **Research steps planned**: 2
- **Research steps completed**: 2
- **Total web searches performed**: 5
- **Reflection triggered correction**: Yes
- **Correction details**: Added Graph RAG implementation details from follow-up search
"""


@pytest.fixture
def sample_report_with_preamble():
    """A report with PAI artifact preamble that should be stripped."""
    return """\
════ PAI | ALGORITHM MODE ════════════════════

Some other preamble text here.

## Research Plan

| Step | Research Question |
|------|------------------|
| 1 | What is X? |

## Report

Content here.
"""
