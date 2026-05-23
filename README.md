# AI Research Agent

An AI-powered research assistant that autonomously searches the web and generates comprehensive, cited research reports on any topic.

Built with **Claude Sonnet** (Anthropic) + **DuckDuckGo** search + **LangGraph** ReAct agent + **Streamlit** UI.

---

## Features

- **Autonomous web research** — agent performs multiple targeted searches, not just a single query
- **Structured reports** — every report includes executive summary, key findings, detailed analysis, and sources
- **Two depth modes** — Quick (3 sources, ~30s) or Deep (7 sources, ~60s)
- **Research history** — all reports saved locally to SQLite; reload any past report instantly
- **Download reports** — export any report as a `.md` file
- **Clean UI** — Streamlit-based, runs in the browser

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet (`claude-sonnet-4-6`) via Anthropic API |
| Agent Framework | LangGraph `create_react_agent` (ReAct loop) |
| Web Search | DuckDuckGo Search (free, no API key) |
| Frontend | Streamlit |
| Database | SQLite (via Python stdlib) |
| Deployment | Streamlit Community Cloud |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/harshlotia/ai-research-agent.git
cd ai-research-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API key

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

- **Anthropic API key** → [console.anthropic.com](https://console.anthropic.com/)

> DuckDuckGo search is free and requires no API key.

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Project Structure

```
ai-research-agent/
├── app.py                  # Streamlit UI
├── agent/
│   ├── __init__.py
│   └── researcher.py       # LangGraph ReAct agent + system prompt
├── utils/
│   ├── __init__.py
│   └── database.py         # SQLite history (save / load / delete reports)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## How It Works

```
User query
    │
    ▼
LangGraph ReAct Agent (Claude Sonnet)
    │
    ├─► DuckDuckGo Search (call 1) ──► results
    ├─► DuckDuckGo Search (call 2) ──► results
    ├─► DuckDuckGo Search (call 3) ──► results
    │          ...
    ▼
Synthesize all results into structured markdown report
    │
    ▼
Save to SQLite  ──►  Display in Streamlit UI
```

The agent uses a [ReAct](https://arxiv.org/abs/2210.03629) loop — it reasons about what to search next based on what it found so far, not just a single query.

---

## Deploy to Streamlit Community Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app**
3. Select your repo and set **Main file** to `app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "your_key"
   ```
5. Click **Deploy**

---

