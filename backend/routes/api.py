import json
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models import ExtractRequest, ChatRequest

from utils.session_storage import session_store

router = APIRouter()

_youtube_extractor = None
_instagram_extractor = None


try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]

        def decorator(func):
            return func

        return decorator


def get_youtube_extractor():
    global _youtube_extractor

    if _youtube_extractor is None:
        from utils.YouTubeExtraction import YouTubeExtractor

        _youtube_extractor = YouTubeExtractor()

    return _youtube_extractor


def get_instagram_extractor():
    global _instagram_extractor

    if _instagram_extractor is None:
        from utils.InstagramExtraction import InstagramExtractor

        _instagram_extractor = InstagramExtractor()

    return _instagram_extractor


def get_chat_graph():
    from graph import graph

    return graph


def summarize_extract_inputs(inputs: dict) -> dict:

    request = inputs.get("request")

    if request is None:
        return inputs

    return {
        "video_a_url": request.video_a_url,
        "video_b_url": request.video_b_url
    }


def summarize_extract_outputs(output: dict) -> dict:

    if not output:
        return {}

    return {
        "session_id": output.get("session_id"),
        "video_a_platform": output.get("video_a_platform"),
        "video_b_platform": output.get("video_b_platform"),
        "video_a_title": output.get("video_a_title"),
        "video_b_title": output.get("video_b_title"),
        "video_a_transcript_available": (
            output.get("video_a_data", {})
            .get("transcript_available")
        ),
        "video_b_transcript_available": (
            output.get("video_b_data", {})
            .get("transcript_available")
        )
    }


def summarize_video_inputs(inputs: dict) -> dict:

    return {
        "url": inputs.get("url"),
        "label": inputs.get("label")
    }


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


@traceable(
    name="extract_video",
    run_type="tool",
    process_inputs=summarize_video_inputs,
    process_outputs=lambda output: summarize_video_data(output)
)
def extract_video(url: str, label: str) -> dict:

    try:
        platform = detect_platform(url)

        if platform == "youtube":
            data = get_youtube_extractor().extract(url)
            data["platform"] = "youtube"
            data["video_label"] = label
            return data

        data = get_instagram_extractor().extract(
            url,
            generate_transcript=True
        )
        data["platform"] = "instagram"
        data["video_label"] = label
        return data

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc


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


def summarize_video_data(video_data: dict) -> dict:

    if not video_data:
        return {}

    metadata = video_data.get("metadata", {})
    text = get_video_text(video_data)

    return {
        "platform": video_data.get("platform"),
        "video_label": video_data.get("video_label"),
        "title": get_display_title(video_data),
        "source_id": get_source_id(
            video_data,
            video_data.get("video_label", "unknown")
        ),
        "transcript_available": bool(video_data.get("transcript")),
        "text_length": len(text),
        "views": metadata.get("view_count") or metadata.get("views"),
        "likes": metadata.get("like_count") or metadata.get("likes"),
        "comments": metadata.get("comment_count") or metadata.get("comments")
    }


def calculate_engagement_rate(metadata: dict) -> float | None:

    views = metadata.get("view_count") or metadata.get("views")
    likes = metadata.get("like_count") or metadata.get("likes") or 0
    comments = metadata.get("comment_count") or metadata.get("comments") or 0

    if not views:
        return None

    return round(
        ((likes + comments) / views) * 100,
        2
    )


def ensure_engagement_rate(video_data: dict) -> dict:

    metadata = video_data.get("metadata", {})

    if metadata.get("engagement_rate") is None:
        metadata["engagement_rate"] = calculate_engagement_rate(metadata)

    return video_data


def get_metrics(video_data: dict) -> dict:

    metadata = video_data.get("metadata", {})
    engagement_rate = metadata.get("engagement_rate")

    if engagement_rate is None:
        engagement_rate = calculate_engagement_rate(metadata)

    return {
        "platform": video_data.get("platform"),
        "title": get_display_title(video_data),
        "thumbnail": metadata.get("thumbnail"),
        "channel": metadata.get("channel") or metadata.get("owner_username"),
        "follower_count": metadata.get("follower_count"),
        "views": metadata.get("view_count") or metadata.get("views"),
        "likes": metadata.get("like_count") or metadata.get("likes"),
        "comments": metadata.get("comment_count") or metadata.get("comments"),
        "duration_seconds": metadata.get("duration_seconds") or metadata.get("video_duration"),
        "upload_date": metadata.get("upload_date"),
        "engagement_rate": engagement_rate,
        "tags": metadata.get("tags") or metadata.get("hashtags") or [],
        "mentions": metadata.get("mentions") or [],
    }


def get_client_video_data(video_data: dict) -> dict:

    return {
        "platform": video_data.get("platform"),
        "title": get_display_title(video_data),
        "metrics": get_metrics(video_data),
        "metadata": video_data.get("metadata", {}),
        "transcript": video_data.get("transcript"),
        "hook_text": video_data.get("hook_text"),
        "transcript_source": video_data.get("transcript_source"),
        "transcript_available": bool(video_data.get("transcript"))
    }


@traceable(name="store_video_documents", run_type="retriever", process_inputs=lambda inputs: summarize_video_data(inputs["video_data"]))
def store_video_documents(video_data: dict) -> None:
    from rag.vector_store import store_documents

    text = get_video_text(video_data)

    if not text.strip():
        return {
            "stored": False,
            "reason": "No text available to store."
        }

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

    return {
        "stored": True,
        "collection_name": "social_content",
        "document_id": label,
        "chunk_metadata": chunk_metadata
    }


@router.post("/extract")
@traceable(
    name="extract_content",
    run_type="chain",
    tags=["auracle", "extract"],
    process_inputs=summarize_extract_inputs,
    process_outputs=summarize_extract_outputs
)
def extract_content(request: ExtractRequest):

    session_id = session_store.create_session()

    video_a_data = extract_video(
        request.video_a_url,
        "A"
    )
    video_a_data = ensure_engagement_rate(video_a_data)

    video_b_data = extract_video(
        request.video_b_url,
        "B"
    )
    video_b_data = ensure_engagement_rate(video_b_data)

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
        "instagram_shortcode": get_display_title(video_b_data),
        "video_a_data": get_client_video_data(video_a_data),
        "video_b_data": get_client_video_data(video_b_data)
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

    result = get_chat_graph().invoke(
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
        "response": result["response"],
        "citations": result.get("citations", [])
    }


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):

    session = session_store.get_session(
        request.session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    result = get_chat_graph().invoke(
        {
            "session_id": request.session_id,
            "user_query": request.query
        },
        config={
            "run_name": "auracle_chat_graph_stream",
            "tags": [
                "auracle",
                "chat",
                "langgraph",
                "stream"
            ],
            "metadata": {
                "session_id": request.session_id
            }
        }
    )

    def event_stream():
        for token in re.findall(r"\S+\s*", result["response"]):
            yield f"data: {json.dumps(token)}\n\n"

        yield (
            "event: citations\n"
            f"data: {json.dumps(result.get('citations', []))}\n\n"
        )
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
