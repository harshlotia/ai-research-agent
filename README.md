# AI Research Agent

> Type a topic. Get a full, cited research report in under a minute.

An AI agent that autonomously browses the web and writes a structured research report on any topic — complete with executive summary, key findings, analysis, and sources.

**Live demo → [ai-research-agent-yv74luwzxrurhp8wziarhx.streamlit.app](https://ai-research-agent-yv74luwzxrurhp8wziarhx.streamlit.app/)**

Built with **Claude Sonnet 4** · **LangGraph** · **DuckDuckGo** · **Streamlit**

---

## What it does

1. You type a research topic (e.g. *"Latest breakthroughs in fusion energy"*)
2. The AI agent runs 3–7 targeted web searches, reading results as it goes
3. It synthesizes everything into a clean markdown report — streamed live as it writes
4. The report is saved to your history so you can revisit it anytime

Every report follows the same structure:

```
# Topic Title
## Executive Summary     — 2–3 sentence overview
## Key Findings          — 4–8 bullet points
## Detailed Analysis     — multiple subtopics with depth
## Current Trends        — what it means going forward
## Conclusion            — key takeaways
## Sources               — every URL used
```

---

## Features

| Feature | Details |
|---|---|
| Autonomous research | Agent decides what to search next based on what it found — not a single fixed query |
| Two depth modes | **Quick** (3 sources, ~30s) or **Deep** (7 sources, ~60s) |
| Live streaming | Report text appears word-by-word as Claude writes it |
| Research history | All reports saved to SQLite; click any past report to reload it |
| Per-session isolation | Each browser tab has its own private history |
| Download | Export any report as a `.md` file |
| Free search | Uses DuckDuckGo — no search API key needed |

---

## How it works

The agent uses a **ReAct loop** — it alternates between *reasoning* and *acting* until it has enough information to write the report.

```
Your query
    │
    ▼
Claude thinks: "I should search for X"
    └─► DuckDuckGo search ──► results fed back to Claude
Claude thinks: "Now I need Y"
    └─► DuckDuckGo search ──► results fed back to Claude
                ... (repeats 3–7 times)
Claude writes the full report
    │
    ▼
Streamed live to your browser + saved to SQLite
```

This is fundamentally different from a chatbot — the agent *plans and adapts* its searches based on what it discovers, rather than querying once and guessing.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet 4 (`claude-sonnet-4-6`) via Anthropic API |
| Agent framework | LangGraph `create_react_agent` |
| Web search | DuckDuckGo (free, no API key) |
| UI | Streamlit |
| Storage | SQLite (Python stdlib) |
| Deployment | Streamlit Community Cloud |

---

## Quick start

### Prerequisites
- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/) (Claude access)

### 1. Clone

```bash
git clone https://github.com/harshlotia/ai-research-agent.git
cd ai-research-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and set:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 5. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Project structure

```
ai-research-agent/
├── app.py                  # Streamlit UI — layout, forms, history sidebar
├── agent/
│   └── researcher.py       # LangGraph ReAct agent + streaming logic
├── utils/
│   └── database.py         # SQLite helpers (save / load / delete reports)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Deploy to Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app**
3. Select your repo, set **Main file** to `app.py`
4. Open **Advanced settings → Secrets** and add:
   ```toml
   ANTHROPIC_API_KEY = "your_key_here"
   ```
5. Click **Deploy** — done

> **Note:** Streamlit Cloud's filesystem is ephemeral. Research history won't survive redeployments. For persistent history, swap SQLite for a hosted database (e.g. Supabase, PlanetScale).

---
