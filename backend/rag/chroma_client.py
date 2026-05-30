import chromadb
from chromadb.api.models.Collection import Collection


KNOWLEDGE_BASE_COLLECTION = "knowledge_base"
SOCIAL_CONTENT_COLLECTION = "social_content"


_client = None
_knowledge_collection = None
_content_collection = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Return the singleton ChromaDB client.
    """

    global _client

    if _client is None:
        _client = chromadb.PersistentClient(
            path="./chroma_db"
        )

    return _client


def get_knowledge_collection() -> Collection:
    """
    Return the knowledge base collection.
    """

    global _knowledge_collection

    if _knowledge_collection is None:
        client = get_chroma_client()

        _knowledge_collection = client.get_or_create_collection(
            name=KNOWLEDGE_BASE_COLLECTION
        )

    return _knowledge_collection


def get_content_collection() -> Collection:
    """
    Return the social content collection.
    """

    global _content_collection

    if _content_collection is None:
        client = get_chroma_client()

        _content_collection = client.get_or_create_collection(
            name=SOCIAL_CONTENT_COLLECTION
        )

    return _content_collection


def clear_knowledge_base() -> None:
    """
    Completely reset the knowledge base collection.
    """

    global _knowledge_collection

    client = get_chroma_client()

    try:
        client.delete_collection(
            name=KNOWLEDGE_BASE_COLLECTION
        )
    except Exception:
        pass

    _knowledge_collection = client.get_or_create_collection(
        name=KNOWLEDGE_BASE_COLLECTION
    )


def clear_social_content() -> None:
    """
    Completely reset the social content collection.
    """

    global _content_collection

    client = get_chroma_client()

    try:
        client.delete_collection(
            name=SOCIAL_CONTENT_COLLECTION
        )
    except Exception:
        pass

    _content_collection = client.get_or_create_collection(
        name=SOCIAL_CONTENT_COLLECTION
    )