import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agent.researcher import run_research
from utils.database import delete_report, get_history, get_report, init_db, save_report

# Load .env for local dev; Streamlit Cloud uses st.secrets
load_dotenv()

# Expose Streamlit Cloud secrets as env vars so the agent can read them
if not os.getenv("ANTHROPIC_API_KEY"):
    try:
        _val = st.secrets.get("ANTHROPIC_API_KEY")
        if _val:
            os.environ["ANTHROPIC_API_KEY"] = _val
    except Exception:
        pass

init_db()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .report-header { font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
    div[data-testid="stMarkdownContainer"] h1 { border-bottom: 2px solid #667eea; padding-bottom: 0.4rem; }
    div[data-testid="stMarkdownContainer"] h2 { color: #4a5568; }
    div[data-testid="stMarkdownContainer"] h3 { color: #667eea; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Research Agent")
    st.caption("Powered by Claude + DuckDuckGo")
    st.divider()

    st.subheader("⚙️ Settings")
    depth_option = st.selectbox(
        "Research depth",
        ["Quick — 3 sources (~30s)", "Deep — 7 sources (~60s)"],
        help="Deep mode runs more searches for richer reports",
    )
    depth = "deep" if depth_option.startswith("Deep") else "quick"

    st.divider()
    st.subheader("📚 History")

    history = get_history(limit=15)
    if history:
        for item in history:
            label = item["query"][:38] + "…" if len(item["query"]) > 38 else item["query"]
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"h_{item['id']}", use_container_width=True):
                    st.session_state.current_report = item["report"]
                    st.session_state.current_query = item["query"]
                    st.session_state.current_depth = item["depth"]
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"d_{item['id']}"):
                    delete_report(item["id"])
                    if st.session_state.get("current_query") == item["query"]:
                        st.session_state.pop("current_report", None)
                        st.session_state.pop("current_query", None)
                    st.rerun()
    else:
        st.caption("No history yet — run your first research!")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("AI Research Agent")
st.markdown("Enter any topic or question and I'll search the web, read the sources, and write you a full report.")

st.divider()

query = st.text_area(
    "What do you want to research?",
    placeholder="e.g.  Latest breakthroughs in fusion energy\n     How does the CRISPR gene editing work?\n     State of the electric vehicle market in 2025",
    height=100,
)

col_run, col_tip = st.columns([2, 5])
with col_run:
    run_clicked = st.button("🚀  Start Research", type="primary", use_container_width=True)
with col_tip:
    st.markdown(
        "<small style='color:#888'>Try: <em>AI agent frameworks 2025</em> · "
        "<em>Impact of microplastics on human health</em> · "
        "<em>How does Transformer architecture work</em></small>",
        unsafe_allow_html=True,
    )

# ── Validation & run ──────────────────────────────────────────────────────────
if run_clicked:
    if not query.strip():
        st.warning("Please enter a research topic or question.")
    elif not os.getenv("ANTHROPIC_API_KEY"):
        st.error("ANTHROPIC_API_KEY missing — add it to your `.env` file.")
    else:
        with st.spinner(f"Searching the web and writing your report… (this takes ~{30 if depth == 'quick' else 60}s)"):
            try:
                result = run_research(query.strip(), depth=depth)
                save_report(query.strip(), depth, result["report"])
                st.session_state.current_report = result["report"]
                st.session_state.current_query = query.strip()
                st.session_state.current_depth = depth
                st.rerun()
            except Exception as e:
                st.error(f"Research failed: {e}")
                st.info("Double-check your API keys in `.env` and try again.")

# ── Report display ────────────────────────────────────────────────────────────
if st.session_state.get("current_report"):
    st.divider()

    depth_label = "Deep" if st.session_state.get("current_depth") == "deep" else "Quick"
    st.markdown(
        f"<p class='report-header'>{depth_label} research · "
        f"generated {datetime.now().strftime('%b %d, %Y %H:%M')}</p>",
        unsafe_allow_html=True,
    )

    col_title, col_dl = st.columns([6, 1])
    with col_title:
        st.subheader(st.session_state["current_query"])
    with col_dl:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download",
            data=st.session_state["current_report"],
            file_name=f"research_{ts}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown(st.session_state["current_report"])
