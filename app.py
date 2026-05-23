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
    st.caption("History")

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
        st.caption("No searches yet.")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("AI Research Agent")
st.caption("Enter any topic or question — I'll search the web and write you a full cited report.")
st.divider()

with st.form("research_form"):
    query = st.text_area(
        "What do you want to research?",
        placeholder="e.g. Latest breakthroughs in fusion energy",
        height=100,
        label_visibility="collapsed",
    )
    col_depth, col_btn = st.columns([1, 2])
    with col_depth:
        depth_option = st.selectbox(
            "Depth",
            ["Quick — 3 sources (~30s)", "Deep — 7 sources (~60s)"],
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.form_submit_button("🚀  Start Research", type="primary", use_container_width=True)

depth = "deep" if depth_option.startswith("Deep") else "quick"

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
