# backend/graph.py

import os
from typing import Any, Callable, TypedDict, Optional

from dotenv import load_dotenv

load_dotenv()

if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

if os.getenv("LANGSMITH_PROJECT") and not os.getenv("LANGCHAIN_PROJECT"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT")

if os.getenv("LANGSMITH_ENDPOINT") and not os.getenv("LANGCHAIN_ENDPOINT"):
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")

from langgraph.graph import StateGraph, END

from utils.TextModel import TextModel
from utils.session_storage import session_store

from rag.vector_store import retrieve_documents

from schemas import QueryClassification

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]

        def decorator(func: Callable):
            return func

        return decorator


# ============================================================
# MODELS
# ============================================================

_text_model = None


def get_text_model() -> TextModel:

    global _text_model

    if _text_model is None:
        _text_model = TextModel()

    return _text_model


# ============================================================
# STATE
# ============================================================

class GraphState(TypedDict):
    session_id: str
    user_query: str

    session_data: Optional[dict]

    classification: Optional[QueryClassification]
    classification_trace: Optional[dict]

    retrieved_context: Optional[str]
    retrieved_sources: Optional[list[dict]]
    rag_accessed: Optional[bool]
    rag_collection: Optional[str]
    rag_document_count: Optional[int]

    response: Optional[str]
    citations: Optional[list[dict]]
    response_trace: Optional[dict]


def serialize_classification(classification: QueryClassification) -> dict[str, Any]:

    return {
        "intent": classification.intent.value,
        "use_rag": classification.use_rag,
        "collection_name": classification.collection_name
    }


# ============================================================
# NODE 1
# LOAD SESSION
# ============================================================

@traceable(name="load_session", run_type="chain")
def load_session(state: GraphState):

    session = session_store.get_session(
        state["session_id"]
    )

    if session is None:
        raise ValueError(
            f"Session not found: {state['session_id']}"
        )

    return {
        "session_data": session
    }


# ============================================================
# NODE 2
# CLASSIFY QUERY
# ============================================================

@traceable(name="classify_query", run_type="chain")
def classify_query(state: GraphState):

    classification = get_text_model().classify_query(
        state["user_query"]
    )

    classification_trace = serialize_classification(classification)

    return {
        "classification": classification,
        "classification_trace": classification_trace,
        "rag_accessed": classification.use_rag,
        "rag_collection": classification.collection_name,
        "rag_document_count": 0
    }


# ============================================================
# NODE 3
# RETRIEVE CONTEXT
# ============================================================

@traceable(name="retrieve_context", run_type="retriever")
def retrieve_context_node(state: GraphState):

    classification = state["classification"]

    if not classification.use_rag:
        return {
            "retrieved_context": "",
            "retrieved_sources": [],
            "rag_accessed": False,
            "rag_collection": None,
            "rag_document_count": 0
        }

    docs = retrieve_documents(
        query=state["user_query"],
        collection_name=classification.collection_name
    )

    context = "\n\n".join(
        [
            f"[Video {doc['metadata'].get('video_id', 'unknown')} "
            f"chunk {doc['metadata'].get('chunk_index', 'unknown')}]\n"
            f"{doc['document']}"
            for doc in docs
        ]
    )

    sources = [
        {
            "video_id": doc["metadata"].get("video_id"),
            "chunk_index": doc["metadata"].get("chunk_index"),
            "platform": doc["metadata"].get("platform"),
            "title": doc["metadata"].get("title"),
            "source_id": doc["metadata"].get("source_id"),
            "excerpt": doc["document"][:240],
            "distance": doc["distance"]
        }
        for doc in docs
    ]

    return {
        "retrieved_context": context,
        "retrieved_sources": sources,
        "rag_accessed": True,
        "rag_collection": classification.collection_name,
        "rag_document_count": len(docs)
    }


# ============================================================
# NODE 4
# GENERATE RESPONSE
# ============================================================

@traceable(name="generate_response", run_type="llm")
def generate_response(state: GraphState):

    classification = state["classification"]

    session_data = state["session_data"]

    query = state["user_query"]
    generation_path = "standard_answer"

    if classification.intent.value == "comparison":
        generation_path = "comparison"

        response = get_text_model().compare_content(
            video_a_data=session_data.get("video_a_data") or session_data["youtube_data"],
            video_b_data=session_data.get("video_b_data") or session_data["instagram_data"],
            question=query
        )

        session_store.update_session(
            state["session_id"],
            comparison_result=response
        )

    elif classification.use_rag:
        generation_path = "rag_answer"

        response = get_text_model().answer_question_with_rag(
            question=query,
            session_context=session_data,
            retrieved_context=state["retrieved_context"],
            retrieved_sources=state.get("retrieved_sources") or []
        )

    else:

        response = get_text_model().answer_question(
            question=query,
            session_context=session_data
        )

    session_store.add_message(
        state["session_id"],
        role="user",
        content=query
    )

    session_store.add_message(
        state["session_id"],
        role="assistant",
        content=response
    )

    return {
        "response": response,
        "citations": state.get("retrieved_sources") or [],
        "response_trace": {
            "generation_path": generation_path,
            "intent": classification.intent.value,
            "rag_accessed": bool(state.get("rag_accessed")),
            "rag_collection": state.get("rag_collection"),
            "rag_document_count": state.get("rag_document_count"),
            "citations": state.get("retrieved_sources") or [],
            "message": response
        }
    }


# ============================================================
# ROUTER
# ============================================================

@traceable(name="route_after_classification", run_type="chain")
def route_after_classification(state: GraphState):

    classification = state["classification"]

    if classification.use_rag:
        return "retrieve_context"

    return "generate_response"


# ============================================================
# BUILD GRAPH
# ============================================================

builder = StateGraph(GraphState)

builder.add_node(
    "load_session",
    load_session
)

builder.add_node(
    "classify_query",
    classify_query
)

builder.add_node(
    "retrieve_context",
    retrieve_context_node
)

builder.add_node(
    "generate_response",
    generate_response
)

builder.set_entry_point(
    "load_session"
)

builder.add_edge(
    "load_session",
    "classify_query"
)

builder.add_conditional_edges(
    "classify_query",
    route_after_classification,
    {
        "retrieve_context": "retrieve_context",
        "generate_response": "generate_response"
    }
)

builder.add_edge("retrieve_context","generate_response")
builder.add_edge("generate_response",END)

graph = builder.compile()
