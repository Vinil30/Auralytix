from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rag.vector_store import store_documents
from rag.chroma_client import clear_knowledge_base


KNOWLEDGE_BASE_DIR = PROJECT_DIR / "RAG_INGESTION_DATA"
CHROMA_DB_DIR = BACKEND_DIR / "chroma_db"


def debug(message: str) -> None:
    print(f"[pre_ingestion] {message}", flush=True)


def ingest_markdown_file(file_path: Path) -> None:
    """
    Ingest a single markdown file into the knowledge base.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {file_path}"
        )
    content = file_path.read_text(encoding="utf-8")
    debug(
        f"Ingesting {file_path.name} "
        f"({len(content):,} characters)"
    )
    store_documents(
        document_id=file_path.stem,
        collection_name="knowledge_base",
        text=content,
        metadata={
            "source": "knowledge_base",
            "document_name": file_path.stem
        }
    )


def ingest_all_markdown_files(
    knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR) -> None:
    """
    Ingest all markdown files from the knowledge base directory.
    """
    if not knowledge_base_dir.exists():
        raise FileNotFoundError(
            f"Knowledge base directory not found: {knowledge_base_dir}"
        )

    markdown_files = sorted(knowledge_base_dir.glob("*.md"))
    debug(f"Found {len(markdown_files)} markdown file(s).")

    if not markdown_files:
        raise FileNotFoundError(
            f"No markdown files found in: {knowledge_base_dir}"
        )

    for file_path in markdown_files:
        ingest_markdown_file(file_path)
        debug(f"Stored {file_path.stem} in knowledge_base.")

def main() -> None:
    """
    Clear existing knowledge base and re-ingest all markdown files.
    """

    debug(f"Project directory: {PROJECT_DIR}")
    debug(f"Backend directory: {BACKEND_DIR}")
    debug(f"Expected Chroma DB directory: {CHROMA_DB_DIR}")
    debug(f"Knowledge source directory: {KNOWLEDGE_BASE_DIR}")
    debug(f"Current working directory: {Path.cwd()}")
    debug("Clearing existing knowledge_base collection.")
    clear_knowledge_base()
    ingest_all_markdown_files()
    debug("Knowledge base ingestion completed.")

if __name__ == "__main__":
    main()
