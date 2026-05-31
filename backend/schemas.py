from enum import Enum
from pydantic import BaseModel


class Intent(str, Enum):
    COMPARISON = "comparison"
    TRANSCRIPT_QA = "transcript_qa"
    RECOMMENDATION = "recommendation"


class QueryClassification(BaseModel):
    intent: Intent
    use_rag: bool
    collection_name: str | None = None