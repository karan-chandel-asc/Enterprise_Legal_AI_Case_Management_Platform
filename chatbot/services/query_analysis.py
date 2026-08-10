"""Groq-backed query analysis for semantic search.

1. Classify the input as a greeting / chitchat vs a case-related search.
2. Extract highlight keywords for matching snippets in the results.
"""

from __future__ import annotations

import json
import os
import re

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger

# Fast, cheap model — only needs classification + keyword extraction.
MODEL_NAME = "llama-3.1-8b-instant"

GREETING_REPLY = (
    "Please ask a case-related query — for example evidence, witness statements, "
    "hearing dates, contract clauses, or FIR details. Greetings and general chat "
    "won't search your documents."
)

_SYSTEM = """You analyze search queries for a legal case-management app.
Return ONLY valid JSON with this shape:
{"query_type":"greeting"|"case_related","keywords":["word1","word2"]}

Rules:
- query_type=greeting for hellos, thanks, how are you, ok, bye, or any non-legal chitchat with no searchable case topic.
- query_type=case_related for anything about cases, documents, evidence, parties, courts, hearings, laws, contracts, FIRs, etc.
- keywords: 2-8 important searchable terms from the query (nouns, names, legal concepts). Lowercase. No filler words (the, a, is, please, find, show, me).
- If greeting, keywords must be [].
"""

_GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|hii+|helo|howdy|good\s*(morning|afternoon|evening)|"
    r"thanks|thank\s*you|ty|ok|okay|bye|goodbye|sup|yo|how\s+are\s+you|"
    r"what'?s\s+up|whats\s+up)[\s!.?]*$",
    re.IGNORECASE,
)


def _heuristic_analyze(query: str) -> dict:
    """Offline fallback when Groq is unavailable."""
    q = (query or "").strip()
    if not q or _GREETING_RE.match(q):
        return {"query_type": "greeting", "keywords": []}

    stop = {
        "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "to", "for",
        "and", "or", "with", "from", "about", "find", "show", "me", "please", "any",
        "all", "what", "where", "when", "who", "which", "how", "does", "did", "do",
    }
    keywords = []
    for raw in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{1,}", q.lower()):
        if raw in stop or len(raw) < 3:
            continue
        if raw not in keywords:
            keywords.append(raw)
        if len(keywords) >= 8:
            break

    if not keywords and len(q.split()) <= 2:
        return {"query_type": "greeting", "keywords": []}
    return {"query_type": "case_related", "keywords": keywords}


def analyze_search_query(query: str) -> dict:
    """Return {"query_type": str, "keywords": list[str]}."""
    query = (query or "").strip()
    if not query:
        return {"query_type": "greeting", "keywords": []}

    # Cheap fast-path for obvious greetings — skip the LLM round-trip.
    if _GREETING_RE.match(query):
        return {"query_type": "greeting", "keywords": []}

    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatGroq(
            model=MODEL_NAME,
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=f"Query: {query}"),
        ])
        raw = (getattr(resp, "content", None) or "").strip()
        # Model sometimes wraps JSON in fences.
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        qtype = data.get("query_type", "case_related")
        if qtype not in {"greeting", "case_related"}:
            qtype = "case_related"
        keywords = []
        for k in data.get("keywords") or []:
            word = str(k).strip().lower()
            if word and word not in keywords:
                keywords.append(word)
        return {"query_type": qtype, "keywords": keywords[:8]}
    except Exception as e:
        logger.warning(f"[SearchAnalyze] Groq analyze failed, using heuristic: {e}")
        return _heuristic_analyze(query)
