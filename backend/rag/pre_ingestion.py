from pathlib import Path

from rag.vector_store import store_documents
from rag.chroma_client import clear_knowledge_base


KNOWLEDGE_BASE_DIR = Path("knowledge_base")


def ingest_markdown_file(file_path: Path) -> None:
    """
    Ingest a single markdown file into the knowledge base.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {file_path}"
        )
    content = file_path.read_text(encoding="utf-8")
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
    for file_path in knowledge_base_dir.glob("*.md"):
        ingest_markdown_file(file_path)

def main() -> None:
    """
    Clear existing knowledge base and re-ingest all markdown files.
    """

    clear_knowledge_base()
    ingest_all_markdown_files()

if __name__ == "__main__":
    main()