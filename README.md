# Managed Agent PoC — Research Agent

Autonomous Research Agents built with the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk-overview) (`claude-agent-sdk`). Three demos showing progressively more sophisticated agent patterns: single agent, multi-agent orchestration, and n8n hybrid integration.

Part of the [KI-Roadmap P3](../KI-Roadmap/Plans/P3-Managed-Agent-PoC-Spec.md) project.

## Demos Overview

| Demo | Script | Pattern | Description |
|------|--------|---------|-------------|
| 1 | `research_agent.py` | Single agent | One agent researches topic end-to-end |
| 2 | `multi_agent_research.py` | Multi-agent | Orchestrator spawns parallel sub-agents per subtopic |
| 3 | `n8n_hybrid_server.py` | HTTP API + n8n | Webhook triggers research, n8n formats and emails |
| 4 | `plan_reflect_agent.py` | Plan + Reflect | Structured planning, sequential execution, self-critique |

## Prerequisites

- **Python 3.12+**
- **Claude Code CLI** installed and authenticated (`npm install -g @anthropic-ai/claude-code`)
- **Anthropic API access** (the CLI handles authentication — no manual API key export needed)
- **n8n** (optional, for Demo 3 email workflow) — v2.11+ installed locally

## Setup

```bash
cd ~/projects/managed-agent-poc

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install claude-agent-sdk anthropic
```

---

## Demo 1: Simple Research Agent

Single agent that researches a topic autonomously and produces a structured Markdown report.

### Architecture

```
[CLI: topic string]
        |
        v
+-- claude-agent-sdk (query) ------------------+
|                                               |
|  Model: claude-sonnet-4-6                     |
|  Tools: WebSearch, WebFetch                   |
|                                               |
|  1. Decompose topic into 3-5 subtopics        |
|  2. Web search per subtopic                   |
|  3. Evaluate and filter sources               |
|  4. Write structured Markdown report          |
|                                               |
+-----------------------------------------------+
        |
        v
[output/{topic-slug}.md]
```

### Usage

```bash
python3 research_agent.py "State of AI Coding Agents 2026"
python3 research_agent.py "KI-Telefonie im DACH-Mittelstand" -o reports/
```

| Flag | Default | Description |
|------|---------|-------------|
| `topic` (positional) | *required* | The topic to research |
| `-o`, `--output-dir` | `output/` | Directory to save the report |

### Verified Test Results

| Metric | Value |
|--------|-------|
| Report length | 2,463 words |
| Sources | 14 verified URLs |
| Agent turns | 32 |
| Cost | $0.81 |
| Runtime | ~3 minutes |

Tested with topic "State of AI Coding Agents 2026" on 2026-04-10.

---

## Demo 2: Multi-Agent Research

Orchestrator agent decomposes the topic into subtopics and spawns parallel sub-agents — each researching one subtopic independently. Results are stitched into a unified report.

### Architecture

```
[CLI: topic string]
        |
        v
+-- ClaudeSDKClient (streaming) ----------------+
|                                                |
|  Orchestrator Agent (claude-sonnet-4-6)        |
|  "Decompose topic, spawn researchers"          |
|                                                |
|  ┌──────────┐ ┌──────────┐ ┌──────────┐       |
|  │Researcher│ │Researcher│ │Researcher│  ...   |
|  │Subtopic 1│ │Subtopic 2│ │Subtopic 3│       |
|  │WebSearch │ │WebSearch │ │WebSearch │       |
|  │WebFetch  │ │WebFetch  │ │WebFetch  │       |
|  └────┬─────┘ └────┬─────┘ └────┬─────┘       |
|       └─────────────┼───────────┘              |
|                     v                          |
|         Orchestrator stitches report           |
|                                                |
+------------------------------------------------+
        |
        v
[output/multi-{topic-slug}.md]
```

### Usage

```bash
python3 multi_agent_research.py "Claude Managed Agents vs LangChain"
python3 multi_agent_research.py "RAG Architekturen 2026" -o reports/
```

| Flag | Default | Description |
|------|---------|-------------|
| `topic` (positional) | *required* | The topic to research |
| `-o`, `--output-dir` | `output/` | Directory to save the report |

### How It Works

1. **Orchestrator** receives the topic and decomposes it into 3-5 subtopics
2. For each subtopic, spawns a **researcher sub-agent** via the Agent tool
3. Sub-agents run in parallel, each using WebSearch/WebFetch independently
4. Progress tracked via `TaskStartedMessage` and `TaskNotificationMessage`
5. Orchestrator collects all results and writes the final unified report
6. Per-agent token breakdown printed to stdout

### Verified Test Results

| Metric | Value |
|--------|-------|
| Report length | 2,178 words |
| Sub-agents spawned | 5 (parallel) |
| Total tokens | ~65,000 across all agents |
| Cost | $1.70 |
| Runtime | ~7 minutes |

Tested with topic "Claude Managed Agents vs LangChain" on 2026-04-10.

**Sub-agent breakdown from test run:**
| Sub-agent | Tokens |
|-----------|--------|
| Claude Managed Agents architecture | 22,081 |
| LangChain architecture and features | 7,429 |
| Developer experience comparison | 11,440 |
| Performance and production readiness | 12,076 |
| Use cases and adoption trends | 11,811 |

### Key Difference from Demo 1

Demo 1 uses `query()` (one-shot, single agent). Demo 2 uses `ClaudeSDKClient` (streaming, bidirectional) with `AgentDefinition` to define sub-agents that the orchestrator can spawn.

---

## Demo 3: n8n Hybrid

HTTP API server that any client (n8n, curl, Postman) can call to trigger research. Includes an importable n8n workflow that receives a webhook, calls the API, formats the report, and sends it via email.

**Shows: "n8n + Managed Agents = complementary, not competitive"**

### Architecture

```
[n8n Webhook / curl]
        |
        v  POST /research {"topic": "..."}
+-- Starlette/Uvicorn HTTP Server -----+
|                                       |
|  /research  → runs research agent     |
|  /health    → health check            |
|                                       |
+---------------------------------------+
        |
        v  JSON response
[n8n: Format Report → Send Email]
```

### Usage

**Start the server:**

```bash
python3 n8n_hybrid_server.py              # Default: port 8000
python3 n8n_hybrid_server.py --port 9000  # Custom port
```

**Test with curl:**

```bash
# Health check
curl http://localhost:8000/health

# Trigger research (takes ~3 minutes)
curl -X POST http://localhost:8000/research \
     -H "Content-Type: application/json" \
     -d '{"topic": "AI Coding Agents 2026"}'
```

### API Endpoints

#### `POST /research`

Triggers autonomous research on a topic.

**Request:**
```json
{"topic": "State of AI Coding Agents 2026"}
```

**Response (from actual test run):**
```json
{
  "topic": "n8n vs Make.com vs Zapier 2026",
  "report": "# n8n vs Make.com vs Zapier: 2026 Automation Platform Comparison\n...",
  "words": 1956,
  "turns": 18,
  "cost_usd": 0.415,
  "elapsed_seconds": 164.5
}
```

#### `GET /health`

Returns `{"status": "ok", "service": "research-agent"}`.

### n8n Workflow Setup

1. Import `n8n_workflow.json` into n8n (Settings → Import Workflow)
2. Configure SMTP credentials in the "Send Email" node
3. Set `EMAIL_FROM` and `EMAIL_TO` environment variables (or edit the node directly)
4. Ensure the Python server is running on `localhost:8000`
5. Activate the workflow — the webhook is ready at `POST /webhook/research`

**Workflow flow:** Webhook Trigger → HTTP Request (calls Python API) → Format Report → Send Email + Respond to Webhook

| Server Flag | Default | Description |
|-------------|---------|-------------|
| `--port` | `8000` | Port to listen on |
| `--host` | `0.0.0.0` | Host to bind to |

---

## Demo 4: Plan & Reflect Research Agent

Single agent with structured Plan-and-Execute + Reflection patterns. Instead of "research this topic" as a single prompt, the agent first creates a research plan, executes it step-by-step with per-step evaluation, then self-critiques the result before finalizing.

**Inspired by:** Plan-and-Execute and Reflection patterns from the LangGraph ecosystem.

### Architecture

```
[CLI: topic string]
        |
        v
+-- claude-agent-sdk (query) ----------------------------------+
|                                                               |
|  Model: claude-sonnet-4-6                                     |
|  Tools: WebSearch, WebFetch                                   |
|                                                               |
|  PHASE 1 — PLAN                                               |
|  ├── Analyze topic                                            |
|  └── Create 3-5 research steps with specific questions        |
|                                                               |
|  PHASE 2 — EXECUTE                                            |
|  ├── Step 1: Search → Evaluate → Record findings              |
|  ├── Step 2: Search → Evaluate → Record findings              |
|  ├── ...                                                      |
|  └── Synthesize all findings into structured report           |
|                                                               |
|  PHASE 3 — REFLECT                                            |
|  ├── Self-critique: coverage, source quality, contradictions  |
|  ├── If "Needs Improvement": targeted follow-up (max 1 iter)  |
|  └── Output reflection notes + meta-info                      |
|                                                               |
+---------------------------------------------------------------+
        |
        v
[output/plan-reflect-{topic-slug}.md]
  Contains: Research Plan + Report + Reflection Notes + Meta
```

### Usage

```bash
python3 plan_reflect_agent.py "State of AI Coding Agents 2026"
python3 plan_reflect_agent.py "RAG Architekturen 2026" -o reports/
```

| Flag | Default | Description |
|------|---------|-------------|
| `topic` (positional) | *required* | The topic to research |
| `-o`, `--output-dir` | `output/` | Directory to save the output |

### Output Structure

Unlike Demo 1 which outputs only the report, Demo 4 outputs a complete research artifact:

1. **Research Plan** — Table of planned steps with questions and target sources
2. **Report** — Executive Summary, Key Findings, Sources, Conclusions (same structure as Demo 1)
3. **Reflection Notes** — Self-critique: plan coverage, source quality, contradictions, overall assessment
4. **Meta** — Step count, web search count, whether reflection triggered a correction

### Example Output (Plan + Reflection sections)

```markdown
## Research Plan

| Step | Research Question | Target Source Type |
|------|------------------|--------------------|
| 1 | What are the leading AI coding agents in 2026? | News, official docs |
| 2 | How do they compare on code generation quality? | Benchmarks, papers |
| 3 | What enterprise adoption patterns are emerging? | Industry reports |
| 4 | What are the key limitations and risks? | Expert analyses |

## Report
[... standard report content ...]

## Reflection Notes

1. **Plan Coverage**: All 4 steps adequately addressed. Step 3 (enterprise adoption)
   had fewer primary sources than ideal.
2. **Source Quality**: 12 sources, mostly authoritative. 2 blog posts are weaker but
   corroborated by other sources.
3. **Contradictions**: Benchmark results vary by provider — noted in findings.
4. **Overall Assessment**: Adequate

## Meta

- **Research steps planned**: 4
- **Research steps completed**: 4
- **Total web searches performed**: 11
- **Reflection triggered correction**: No
- **Correction details**: N/A
```

### Verified Test Results

All 5 test topics run on 2026-04-13:

| # | Topic | Words | Turns | Cost | Correction |
|---|-------|-------|-------|------|------------|
| 1 | State of AI Coding Agents 2026 | 2,338 | 25 | $0.60 | No |
| 2 | n8n vs Make.com vs Zapier 2026 | 2,145 | 18 | $0.50 | No |
| 3 | KI-Telefonie im DACH-Mittelstand | 2,176 | 32 | $0.82 | No |
| 4 | Claude Managed Agents vs LangChain | 2,588 | 30 | $0.53 | No |
| 5 | RAG Architekturen 2026 | 1,823 | 20 | $0.57 | No |

**Average**: 2,214 words, 25 turns, $0.60 per run. 100% structure compliance (Plan + Report + Reflection + Meta present in all runs).

### Key Differences from Demo 1

| Aspect | Demo 1 (Basic) | Demo 4 (Plan + Reflect) |
|--------|----------------|-------------------------|
| Approach | "Research this topic" one-shot | Structured plan → sequential execution → self-critique |
| Planning | Implicit (agent decides internally) | Explicit plan output before any research |
| Evaluation | None — agent decides when done | Per-step sufficiency check during execution |
| Self-critique | None | Reflection phase with optional correction |
| Output | Report only | Plan + Report + Reflection + Meta |
| Max turns | 30 | 40 |

---

## Report Structure

All demos produce reports with this format:

- **Executive Summary** — 2-3 paragraph overview
- **Key Findings** — One subsection per subtopic with detailed analysis
- **Sources** — Numbered list with titles and URLs
- **Conclusions** — Synthesis of findings, trends, and implications

## Test Topics

| # | Topic | Expected Output | Tested |
|---|-------|-----------------|--------|
| 1 | "State of AI Coding Agents 2026" | ~2000 words, 10+ sources | Demo 1: 2,463w / Demo 4: 2,338w |
| 2 | "n8n vs Make.com vs Zapier 2026" | Comparison table + analysis | Demo 3: 1,956w / Demo 4: 2,145w |
| 3 | "KI-Telefonie im DACH-Mittelstand" | Market analysis, providers, ROI | Demo 4: 2,176w |
| 4 | "Claude Managed Agents vs LangChain" | Technical comparison | Demo 2: 2,178w / Demo 4: 2,588w |
| 5 | "RAG Architekturen 2026: Naive vs Graph vs Wiki" | Architecture guide | Demo 4: 1,823w |

## Key SDK Details

- **`query()`** for one-shot interactions (Demo 1, Demo 3 API, Demo 4 plan+reflect)
- **`ClaudeSDKClient`** for streaming/multi-agent (Demo 2)
- **`AgentDefinition`** to declare sub-agents the orchestrator can spawn
- Tool names are Claude Code built-ins: `WebSearch`, `WebFetch` (not `web_search`)
- `permission_mode="bypassPermissions"` for unattended operation
- Authentication handled by the `claude` CLI — no `ANTHROPIC_API_KEY` export needed

## Tech Stack

| Component | Version |
|-----------|---------|
| Python | 3.12 |
| claude-agent-sdk | 0.1.58 |
| anthropic | 0.93.0 |
| starlette | 1.0.0 |
| uvicorn | 0.44.0 |
| Claude Code CLI | 2.1.101 |
| n8n | 2.11.2 |
| Model | claude-sonnet-4-6 |

## Cost (Verified)

All costs from actual test runs:

| Demo | Cost | Words | Runtime | Topic Tested | Date |
|------|------|-------|---------|--------------|------|
| Demo 1 | $0.81 | 2,463 | ~3 min | State of AI Coding Agents 2026 | 2026-04-10 |
| Demo 2 | $1.70 | 2,178 | ~7 min | Claude Managed Agents vs LangChain | 2026-04-10 |
| Demo 3 | $0.42 | 1,956 | 164s | n8n vs Make.com vs Zapier 2026 | 2026-04-10 |
| Demo 4 | $0.60 avg | 2,214 avg | ~2 min | 5 topics (see Demo 4 results) | 2026-04-13 |

## Project Structure

```
managed-agent-poc/
├── research_agent.py          # Demo 1: Simple Research Agent
├── multi_agent_research.py    # Demo 2: Multi-Agent Research
├── n8n_hybrid_server.py       # Demo 3: n8n Hybrid Server
├── plan_reflect_agent.py      # Demo 4: Plan & Reflect Research Agent
├── n8n_workflow.json          # Demo 3: Importable n8n workflow
├── output/                    # Generated reports
│   ├── state-of-ai-coding-agents-2026.md
│   └── multi-claude-managed-agents-vs-langchain.md
├── venv/                      # Python virtual environment
└── README.md
```

## License

Private project.
