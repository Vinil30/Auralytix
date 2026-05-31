from fastapi import APIRouter, HTTPException

from models import ExtractRequest, ChatRequest

from graph import graph

from utils.session_storage import session_store
from utils.YouTubeExtraction import YouTubeExtractor
from utils.InstagramExtraction import InstagramExtractor

from rag.vector_store import store_documents

router = APIRouter()

youtube_extractor = YouTubeExtractor()
instagram_extractor = InstagramExtractor()


def detect_platform(url: str) -> str:

    normalized_url = url.lower()

    if "youtube.com" in normalized_url or "youtu.be" in normalized_url:
        return "youtube"

    if "instagram.com" in normalized_url:
        return "instagram"

    raise HTTPException(
        status_code=400,
        detail="Only YouTube and Instagram URLs are supported."
    )


def extract_video(url: str, label: str) -> dict:

    platform = detect_platform(url)

    if platform == "youtube":
        data = youtube_extractor.extract(url)
        data["platform"] = "youtube"
        data["video_label"] = label
        return data

    data = instagram_extractor.extract(
        url,
        generate_transcript=False
    )
    data["platform"] = "instagram"
    data["video_label"] = label
    return data


def get_video_text(video_data: dict) -> str:

    transcript = video_data.get("transcript")

    if transcript:
        return transcript

    return (
        video_data.get("metadata", {}).get("caption")
        or ""
    )


def get_source_id(video_data: dict, fallback: str) -> str:

    metadata = video_data.get("metadata", {})

    return str(
        metadata.get("video_id")
        or metadata.get("post_id")
        or metadata.get("shortcode")
        or fallback
    )


def get_display_title(video_data: dict) -> str | None:

    metadata = video_data.get("metadata", {})

    return (
        metadata.get("title")
        or metadata.get("shortcode")
        or metadata.get("caption")
    )


def store_video_documents(video_data: dict) -> None:

    text = get_video_text(video_data)

    if not text.strip():
        return

    label = video_data["video_label"]
    metadata = video_data.get("metadata", {})

    chunk_metadata = {
        "video_id": label,
        "source_id": get_source_id(video_data, label),
        "platform": video_data["platform"],
        "title": metadata.get("title"),
        "shortcode": metadata.get("shortcode")
    }

    chunk_metadata = {
        key: value
        for key, value in chunk_metadata.items()
        if value is not None
    }

    store_documents(
        document_id=label,
        collection_name="social_content",
        text=text,
        metadata=chunk_metadata
    )


@router.post("/extract")
def extract_content(request: ExtractRequest):

    session_id = session_store.create_session()

    video_a_data = extract_video(
        request.video_a_url,
        "A"
    )

    video_b_data = extract_video(
        request.video_b_url,
        "B"
    )

    session_store.update_session(
        session_id,
        video_a_data=video_a_data,
        video_b_data=video_b_data,
        youtube_data=video_a_data,
        instagram_data=video_b_data
    )

    store_video_documents(video_a_data)
    store_video_documents(video_b_data)

    return {
        "session_id": session_id,
        "video_a_platform": video_a_data["platform"],
        "video_b_platform": video_b_data["platform"],
        "video_a_title": get_display_title(video_a_data),
        "video_b_title": get_display_title(video_b_data),
        "youtube_title": get_display_title(video_a_data),
        "instagram_shortcode": get_display_title(video_b_data)
    }


@router.post("/chat")
def chat(request: ChatRequest):

    session = session_store.get_session(
        request.session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    result = graph.invoke(
        {
            "session_id": request.session_id,
            "user_query": request.query
        },
        config={
            "run_name": "auracle_chat_graph",
            "tags": [
                "auracle",
                "chat",
                "langgraph"
            ],
            "metadata": {
                "session_id": request.session_id
            }
        }
    )

    return {
        "response": result["response"]
    }
