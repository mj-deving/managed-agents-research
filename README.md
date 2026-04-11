# Managed Agent PoC — Research Agent

Autonomous Research Agents built with the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/sdk-overview) (`claude-agent-sdk`). Three demos showing progressively more sophisticated agent patterns: single agent, multi-agent orchestration, and n8n hybrid integration.

Part of the [KI-Roadmap P3](../KI-Roadmap/Plans/P3-Managed-Agent-PoC-Spec.md) project.

## Demos Overview

| Demo | Script | Pattern | Description |
|------|--------|---------|-------------|
| 1 | `research_agent.py` | Single agent | One agent researches topic end-to-end |
| 2 | `multi_agent_research.py` | Multi-agent | Orchestrator spawns parallel sub-agents per subtopic |
| 3 | `n8n_hybrid_server.py` | HTTP API + n8n | Webhook triggers research, n8n formats and emails |

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

## Report Structure

All demos produce reports with this format:

- **Executive Summary** — 2-3 paragraph overview
- **Key Findings** — One subsection per subtopic with detailed analysis
- **Sources** — Numbered list with titles and URLs
- **Conclusions** — Synthesis of findings, trends, and implications

## Test Topics

| # | Topic | Expected Output | Tested |
|---|-------|-----------------|--------|
| 1 | "State of AI Coding Agents 2026" | ~2000 words, 10+ sources | Demo 1: 2,463 words, 14 sources |
| 2 | "n8n vs Make.com vs Zapier 2026" | Comparison table + analysis | Demo 3: 1,956 words, 16 sources |
| 3 | "KI-Telefonie im DACH-Mittelstand" | Market analysis, providers, ROI | |
| 4 | "Claude Managed Agents vs LangChain" | Technical comparison | Demo 2: 2,178 words, 5 agents |
| 5 | "RAG Architekturen 2026: Naive vs Graph vs Wiki" | Architecture guide | |

## Key SDK Details

- **`query()`** for one-shot interactions (Demo 1, Demo 3 API)
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

All costs from actual test runs on 2026-04-10:

| Demo | Cost | Words | Runtime | Topic Tested |
|------|------|-------|---------|--------------|
| Demo 1 | $0.81 | 2,463 | ~3 min | State of AI Coding Agents 2026 |
| Demo 2 | $1.70 | 2,178 | ~7 min | Claude Managed Agents vs LangChain |
| Demo 3 | $0.42 | 1,956 | 164s | n8n vs Make.com vs Zapier 2026 |

## Project Structure

```
managed-agent-poc/
├── research_agent.py          # Demo 1: Simple Research Agent
├── multi_agent_research.py    # Demo 2: Multi-Agent Research
├── n8n_hybrid_server.py       # Demo 3: n8n Hybrid Server
├── n8n_workflow.json          # Demo 3: Importable n8n workflow
├── output/                    # Generated reports
│   ├── state-of-ai-coding-agents-2026.md
│   └── multi-claude-managed-agents-vs-langchain.md
├── venv/                      # Python virtual environment
└── README.md
```

## License

Private project.
