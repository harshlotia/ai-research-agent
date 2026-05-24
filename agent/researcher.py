import os
from langchain_anthropic import ChatAnthropic
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """You are an expert research analyst with real-time web search access.

When given a research topic:
1. Perform 3-5 targeted searches to gather comprehensive, up-to-date information
2. Search from multiple angles (overview, recent developments, expert opinions, data/stats)
3. Synthesize everything into a professional research report

Your report MUST follow this exact markdown format:

# [Research Topic Title]

## Executive Summary
[2-3 sentence overview of the most important findings]

## Key Findings
- **[Finding 1]**: Brief explanation
- **[Finding 2]**: Brief explanation
- **[Finding 3]**: Brief explanation
[4-8 total bullet points]

## Detailed Analysis

### [Subtopic 1]
[Detailed paragraph with facts and context from search results]

### [Subtopic 2]
[Detailed paragraph]

### [Subtopic 3]
[Detailed paragraph]

## Current Trends & Implications
[What this means going forward, emerging patterns, future outlook]

## Conclusion
[Concise 2-3 sentence summary of key takeaways]

## Sources
1. [URL] — [brief description of what was found there]
2. [URL] — [brief description]
[List every URL found during research]

Rules:
- Be factual, cite only what search results show
- Aim for 700+ words in the full report
- Always include real URLs in Sources
- Use clear, professional language
- Never make up information not found in search results"""


def stream_research(query: str, depth: str = "quick"):
    """Stream the report token-by-token. Buffers until the # header
    so any brief pre-report reasoning is silently dropped."""
    max_results = 3 if depth == "quick" else 7

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=4096,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    search = DuckDuckGoSearchResults(num_results=max_results)
    agent = create_react_agent(llm, [search])

    buffer = ""
    report_started = False

    for chunk, metadata in agent.stream(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Research this topic thoroughly and produce a detailed report: {query}"),
            ]
        },
        stream_mode="messages",
    ):
        if metadata.get("langgraph_node") == "agent" and hasattr(chunk, "content"):
            content = chunk.content
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = ""

            if not text:
                continue

            if not report_started:
                buffer += text
                if "#" in buffer:
                    report_started = True
                    yield buffer[buffer.find("#"):]
                    buffer = ""
            else:
                yield text

    # Fallback: if the model never emitted a # header, flush whatever we have
    if not report_started and buffer:
        yield buffer


def stream_chat(report: str, history: list, question: str):
    """Stream a conversational answer grounded in the research report."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0.7,
        max_tokens=2048,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    system = (
        "You are a research assistant. The user has just read the following research report "
        "and wants to ask follow-up questions about it.\n\n"
        "RESEARCH REPORT:\n"
        f"{report}\n\n"
        "Answer questions accurately and conversationally. Elaborate on points in the report, "
        "explain concepts, or discuss implications. If a question goes beyond the report, "
        "draw on your general knowledge but say so briefly."
    )

    msgs = [SystemMessage(content=system)]
    for msg in history:
        cls = HumanMessage if msg["role"] == "user" else AIMessage
        msgs.append(cls(content=msg["content"]))
    msgs.append(HumanMessage(content=question))

    for chunk in llm.stream(msgs):
        content = chunk.content
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            yield "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )


def run_research(query: str, depth: str = "quick") -> dict:
    max_results = 3 if depth == "quick" else 7

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=4096,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    search = DuckDuckGoSearchResults(num_results=max_results)

    agent = create_react_agent(llm, [search])

    result = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Research this topic thoroughly and produce a detailed report: {query}"),
        ]
    })

    final_report = result["messages"][-1].content

    return {
        "report": final_report,
        "query": query,
        "depth": depth,
        "steps": len(result["messages"]),
    }
