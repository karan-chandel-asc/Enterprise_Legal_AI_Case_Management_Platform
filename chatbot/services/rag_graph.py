"""LangGraph pipeline that powers the per-case "AI Assistant" chat.

Flow:
    retrieve -> (conditional) -> generate -> END
                             \-> no_context -> END

`retrieve` embeds the question and pulls the top matching chunks for the
case's documents out of Pinecone. If nothing indexed matches, the graph
short-circuits to `no_context` instead of asking the LLM to hallucinate an
answer with no grounding. Otherwise `generate` asks the LLM to answer using
only the retrieved excerpts, citing them by bracket number.
"""

import os
from typing import TypedDict

from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from chatbot.services.embedding import EmbeddingService
from chatbot.services.vector_storage import PineconeService

TOP_K = 6
# llama-3.3-70b-versatile is deprecated by Groq on 2026-08-16; gpt-oss-120b
# is their recommended, higher-quality replacement for RAG/reasoning tasks.
MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are a legal AI assistant helping a lawyer analyze their case documents. "
    "Answer strictly using the numbered context excerpts provided below — never invent facts "
    "that aren't grounded in them. If the excerpts don't contain enough information to answer, "
    "say so plainly instead of guessing. When you use information from an excerpt, cite it inline "
    "with its bracket number, e.g. [1] or [2][3]. Keep answers concise and precise, written for a lawyer."
)


class ChatState(TypedDict):
    question: str
    doc_ids: list[str]
    chat_history: list[dict]
    retrieved: list[dict]
    answer: str
    citations: list[dict]


_llm = None


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(model=MODEL_NAME, api_key=os.getenv("GROQ_API_KEY"), temperature=0.2)
    return _llm


def retrieve_node(state: ChatState) -> dict:
    embedding_service = EmbeddingService()
    query_vec = embedding_service.embed_query(state["question"])
    chunks = PineconeService(embedding_service).query(state["doc_ids"], query_vec, top_k=TOP_K)
    return {"retrieved": chunks}


def _route_after_retrieve(state: ChatState) -> str:
    return "generate" if state.get("retrieved") else "no_context"


def no_context_node(state: ChatState) -> dict:
    return {
        "answer": (
            "I couldn't find anything relevant to that in this case's indexed documents. "
            "Try rephrasing the question, or upload the document that covers this first."
        ),
        "citations": [],
    }


def generate_node(state: ChatState) -> dict:
    retrieved = state["retrieved"]
    context_block = "\n\n".join(
        f"[{i + 1}] ({chunk['doc_name']}, p.{chunk['page']}):\n{chunk['text']}"
        for i, chunk in enumerate(retrieved)
    )
    history_block = "\n".join(
        f"{turn['role'].capitalize()}: {turn['content']}" for turn in state.get("chat_history") or []
    )

    user_prompt = (
        (f"Conversation so far:\n{history_block}\n\n" if history_block else "")
        + f"Context excerpts:\n{context_block}\n\nQuestion: {state['question']}"
    )

    try:
        llm = _get_llm()
        response = llm.invoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
        answer = response.content
    except Exception as e:
        logger.error(f"[RAG] LLM generation failed: {e}")
        answer = "I ran into an error generating a response just now. Please try again in a moment."

    citations = [
        {"doc_name": c["doc_name"], "page": c["page"], "score": round(c["score"], 3)}
        for c in retrieved
    ]
    return {"answer": answer, "citations": citations}


_GRAPH = None


def _build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("no_context", no_context_node)

    graph.set_entry_point("retrieve")
    graph.add_conditional_edges(
        "retrieve", _route_after_retrieve, {"generate": "generate", "no_context": "no_context"}
    )
    graph.add_edge("generate", END)
    graph.add_edge("no_context", END)
    return graph.compile()


def get_rag_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


def run_rag_chat(question: str, doc_ids: list[str], chat_history: list[dict]) -> dict:
    """Run the graph for one question. `chat_history` is prior turns as
    [{"role": "user"|"assistant", "content": str}, ...], oldest first."""
    graph = get_rag_graph()
    result = graph.invoke({
        "question": question,
        "doc_ids": doc_ids,
        "chat_history": chat_history,
        "retrieved": [],
        "answer": "",
        "citations": [],
    })
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "retrieved": result["retrieved"],
    }
