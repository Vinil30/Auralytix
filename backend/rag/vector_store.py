from typing import Any, Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embedding_model import get_embedding_model
from rag.chroma_client import (
    get_knowledge_collection,
    get_content_collection
)


def get_collection(collection_name: str):
    """
    Return the requested ChromaDB collection.
    """
    collection_aliases = {
        "video_analytics": "social_content",
        "video_metrics": "social_content",
        "video_performance": "social_content",
        "performance": "social_content",
        "analytics": "social_content",
        "metrics": "social_content",
        "video_content": "social_content",
        "transcripts": "social_content",
        "transcript": "social_content",
        "social_media": "social_content",
    }

    collection_name = collection_aliases.get(
        collection_name,
        collection_name
    )

    if collection_name == "knowledge_base":
        return get_knowledge_collection()

    if collection_name == "social_content":
        return get_content_collection()

    raise ValueError(
        f"Unsupported collection name: {collection_name}"
    )


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks.
    """

    if not text.strip():
        raise ValueError(
            "Text cannot be empty."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    return splitter.split_text(text)


def generate_embeddings(
    texts: List[str]
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    """

    if not texts:
        raise ValueError(
            "Texts list cannot be empty."
        )

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return embeddings.tolist()


def store_documents(
    document_id: str,
    collection_name: str,
    text: str,
    metadata: Dict[str, Any]
) -> None:
    """
    Store a document in ChromaDB.

    Flow:
        Text
          ↓
        Chunking
          ↓
        Embedding
          ↓
        Storage
    """

    if not document_id.strip():
        raise ValueError(
            "Document ID cannot be empty."
        )

    collection = get_collection(collection_name)

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError(
            f"No chunks generated for document '{document_id}'."
        )

    embeddings = generate_embeddings(chunks)

    ids = [
        f"{document_id}_{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            **metadata,
            "chunk_index": index
        }
        for index in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )


def retrieve_documents(
    query: str,
    collection_name: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most relevant chunks.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if k <= 0:
        raise ValueError(
            "k must be greater than 0."
        )

    collection = get_collection(collection_name)

    query_embedding = generate_embeddings(
        [query]
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    return [
        {
            "document": document,
            "metadata": metadata,
            "distance": distance
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        )
    ]
