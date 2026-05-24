import os
import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from agent.researcher import run_research, stream_chat, stream_research
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

# Assign a unique ID per browser session — persists across reruns within the same tab
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
user_id = st.session_state.user_id

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
    /* Hide the original Ctrl+Enter hint */
    [data-testid="InputInstructions"] { visibility: hidden !important; position: relative !important; }
    /* Show our custom text in its place */
    [data-testid="InputInstructions"]::after {
        content: "Press Enter to submit";
        visibility: visible !important;
        position: absolute !important;
        right: 0; bottom: 0;
        font-size: 0.75rem;
        color: rgba(250,250,250,0.4);
        white-space: nowrap;
    }
    .report-header { font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
    div[data-testid="stMarkdownContainer"] h1 { border-bottom: 2px solid #667eea; padding-bottom: 0.4rem; }
    div[data-testid="stMarkdownContainer"] h2 { color: #4a5568; }
    div[data-testid="stMarkdownContainer"] h3 { color: #667eea; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Research Agent")

    if st.button("+ New Research", use_container_width=True):
        for key in ("current_report", "current_query", "current_depth", "chat_messages"):
            st.session_state.pop(key, None)
        st.session_state["query_input"] = ""
        st.rerun()

    st.divider()
    st.caption("History")

    history = get_history(user_id, limit=15)
    if history:
        for item in history:
            label = item["query"][:38] + "…" if len(item["query"]) > 38 else item["query"]
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"h_{item['id']}", use_container_width=True):
                    st.session_state.current_report = item["report"]
                    st.session_state.current_query = item["query"]
                    st.session_state.current_depth = item["depth"]
                    st.session_state.pop("chat_messages", None)
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"d_{item['id']}"):
                    delete_report(item["id"], user_id)
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
        key="query_input",
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

# Enter → submit,  Shift+Enter / Ctrl+Enter → new line
components.html("""
<script>
(function () {
    function fixHint() {
        try {
            var doc = window.parent.document;
            // Target by data-testid first, fall back to any small with "Ctrl"
            doc.querySelectorAll('[data-testid="InputInstructions"], small').forEach(function (el) {
                if (el.textContent.indexOf('Ctrl') !== -1) {
                    el.textContent = 'Press Enter to submit';
                }
            });
        } catch (e) {}
    }

    // Poll for 15 seconds to catch whenever Streamlit re-renders the element
    var ticks = 0;
    var timer = setInterval(function () {
        fixHint();
        if (++ticks > 75) clearInterval(timer);
    }, 200);

    function setup() {
        try {
            fixHint();
            var doc = window.parent.document;
            doc.querySelectorAll('textarea').forEach(function (ta) {
                if (ta._enterBound) return;
                ta._enterBound = true;
                ta.addEventListener('keydown', function (e) {
                    if (e.key !== 'Enter') return;

                    // Shift+Enter → insert a real newline
                    if (e.shiftKey) {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                        var s = ta.selectionStart, end = ta.selectionEnd;
                        var setter = Object.getOwnPropertyDescriptor(
                            window.parent.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        setter.call(ta, ta.value.slice(0, s) + '\\n' + ta.value.slice(end));
                        ta.selectionStart = ta.selectionEnd = s + 1;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                        return;
                    }

                    // Skip synthetic events (our own re-dispatched Ctrl+Enter)
                    if (!e.isTrusted) return;

                    // Ctrl+Enter → already submits natively, let it through
                    if (e.ctrlKey) return;

                    // Plain Enter → re-dispatch as Ctrl+Enter so Streamlit submits
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    ta.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter', keyCode: 13, ctrlKey: true,
                        bubbles: true, cancelable: true
                    }));
                }, true);
            });
        } catch (err) {}
    }

    setup();
    try {
        new MutationObserver(function () { setup(); fixHint(); }).observe(
            window.parent.document.body,
            { childList: true, subtree: true }
        );
    } catch (err) {}
})();
</script>
""", height=0)

depth = "deep" if depth_option.startswith("Deep") else "quick"

# ── Validation & run ──────────────────────────────────────────────────────────
if run_clicked:
    if not query.strip():
        st.warning("Please enter a research topic or question.")
    elif not os.getenv("ANTHROPIC_API_KEY"):
        st.error("ANTHROPIC_API_KEY missing — add it to your `.env` file.")
    else:
        try:
            st.session_state.pop("chat_messages", None)
            st.caption("Searching the web — report appears as it's written…")
            full_report = st.write_stream(stream_research(query.strip(), depth=depth))
            if not full_report:
                # Streaming yielded nothing — fall back to blocking call
                with st.spinner("Generating report…"):
                    result = run_research(query.strip(), depth=depth)
                full_report = result["report"]
                st.markdown(full_report)
            if full_report:
                save_report(user_id, query.strip(), depth, full_report)
                st.session_state.current_report = full_report
                st.session_state.current_query = query.strip()
                st.session_state.current_depth = depth
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    "📥 Download Report",
                    data=full_report,
                    file_name=f"research_{ts}.md",
                    mime="text/markdown",
                )
            else:
                st.error("No report was generated — please try again.")
        except Exception as e:
            st.error(f"Research failed: {e}")
            st.info("Double-check your API keys in `.env` and try again.")

# ── Report display (history loads / page revisits) ────────────────────────────
if st.session_state.get("current_report") and not run_clicked:
    # (after a fresh run the report was already streamed above; only re-render from history)
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

# ── Follow-up chat ────────────────────────────────────────────────────────────
if st.session_state.get("current_report"):
    st.divider()
    st.caption("Ask follow-up questions about this report")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if question := st.chat_input("Ask anything about this report…"):
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            response = st.write_stream(
                stream_chat(
                    st.session_state["current_report"],
                    st.session_state.chat_messages[:-1],
                    question,
                )
            )

        if response:
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
