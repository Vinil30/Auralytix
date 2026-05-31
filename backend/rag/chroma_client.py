import chromadb
import logging
import shutil
from datetime import datetime
from pathlib import Path
from chromadb.api.shared_system_client import SharedSystemClient
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings


KNOWLEDGE_BASE_COLLECTION = "knowledge_base"
SOCIAL_CONTENT_COLLECTION = "social_content"
CHROMA_DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"
logger = logging.getLogger(__name__)


_client = None
_knowledge_collection = None
_content_collection = None


def _create_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(
            anonymized_telemetry=False
        )
    )


def _backup_chroma_db(reason: BaseException) -> Path | None:
    """
    Move an unreadable Chroma store aside before creating a fresh one.
    """

    if not CHROMA_DB_PATH.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = CHROMA_DB_PATH.with_name(
        f"{CHROMA_DB_PATH.name}_backup_{timestamp}"
    )

    suffix = 1
    while backup_path.exists():
        backup_path = CHROMA_DB_PATH.with_name(
            f"{CHROMA_DB_PATH.name}_backup_{timestamp}_{suffix}"
        )
        suffix += 1

    logger.warning(
        "ChromaDB failed to start from %s (%s). Backing it up to %s.",
        CHROMA_DB_PATH,
        reason,
        backup_path
    )

    shutil.move(
        str(CHROMA_DB_PATH),
        str(backup_path)
    )
    CHROMA_DB_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    return backup_path


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Return the singleton ChromaDB client.
    """

    global _client

    if _client is None:
        try:
            _client = _create_chroma_client()
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise

            _backup_chroma_db(exc)
            SharedSystemClient.clear_system_cache()
            _client = _create_chroma_client()

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
