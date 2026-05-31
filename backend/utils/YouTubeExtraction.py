import os
import re
import tempfile

import yt_dlp
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeExtractor:

    def __init__(self, groq_api_key=None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")

        self.client = None
        if self.groq_api_key:
            self.client = Groq(api_key=self.groq_api_key)

    # ============================================================
    # VIDEO ID EXTRACTION
    # ============================================================

    @staticmethod
    def extract_video_id(video_url: str) -> str:

        patterns = [
            r"(?:v=)([a-zA-Z0-9_-]{11})",
            r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"(?:shorts/)([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)

            if match:
                return match.group(1)

        raise ValueError("Unable to extract YouTube video ID.")

    # ============================================================
    # METADATA EXTRACTION
    # ============================================================

    @staticmethod
    def metadata_extraction(video_url: str) -> dict:

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        views = info.get("view_count") or 0
        likes = info.get("like_count") or 0
        comments = info.get("comment_count") or 0
        engagement_rate = None

        if views > 0:
            engagement_rate = round(
                ((likes + comments) / views) * 100,
                2
            )

        return {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "channel": info.get("channel"),
            "channel_id": info.get("channel_id"),
            "follower_count": (
                info.get("channel_follower_count")
                or info.get("subscriber_count")
            ),
            "description": info.get("description"),
            "duration_seconds": info.get("duration"),
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "engagement_rate": engagement_rate,
            "upload_date": info.get("upload_date"),
            "tags": info.get("tags", []),
            "categories": info.get("categories", []),
            "thumbnail": info.get("thumbnail"),
            "video_url": video_url,
        }

    # ============================================================
    # YOUTUBE TRANSCRIPT API
    # ============================================================

    @staticmethod
    def transcript_extraction(video_url: str) -> str:

        video_id = YouTubeExtractor.extract_video_id(video_url)

        transcript = YouTubeTranscriptApi().fetch(video_id)

        transcript_text = " ".join(
            segment.text
            for segment in transcript
        )

        return transcript_text

    @staticmethod
    def hook_extraction(video_url: str) -> str | None:

        video_id = YouTubeExtractor.extract_video_id(video_url)
        transcript = YouTubeTranscriptApi().fetch(video_id)

        hook_segments = [
            segment.text
            for segment in transcript
            if getattr(segment, "start", 0) < 5
        ]

        hook_text = " ".join(hook_segments).strip()

        return hook_text or None

    # ============================================================
    # FALLBACK STARTS -----  AUDIO DOWNLOAD
    # ============================================================

    @staticmethod
    def download_audio(video_url: str, temp_dir: str) -> str:

        output_template = os.path.join(
            temp_dir,
            "%(id)s.%(ext)s"
        )

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                video_url,
                download=True
            )

            audio_file_path = ydl.prepare_filename(info)

        return audio_file_path

    # ============================================================
    # GROQ WHISPER
    # ============================================================

    def whisper_transcription(self, audio_path: str) -> str:

        if not self.client:
            raise ValueError(
                "Groq client not initialized. "
                "Provide GROQ_API_KEY."
            )

        with open(audio_path, "rb") as audio_file:

            response = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3"
            )

        return response.text

    # ============================================================
    # TRANSCRIPT WITH FALLBACK
    # ============================================================

    def get_transcript(self, video_url: str) -> dict:

        try:

            transcript = self.transcript_extraction(video_url)

            return {
                "source": "youtube_transcript_api",
                "transcript": transcript
            }

        except Exception as transcript_error:

            print(
                f"Transcript API failed. "
                f"Using Whisper fallback.\n"
                f"Reason: {transcript_error}"
            )

            if not self.client:
                raise RuntimeError(
                    "Transcript API failed and "
                    "Groq client is unavailable."
                )

            with tempfile.TemporaryDirectory() as temp_dir:

                audio_path = self.download_audio(
                    video_url,
                    temp_dir
                )

                transcript = self.whisper_transcription(
                    audio_path
                )

                return {
                    "source": "groq_whisper",
                    "transcript": transcript
                }


    def extract(self, video_url: str) -> dict:

        metadata = self.metadata_extraction(video_url)

        transcript_data = self.get_transcript(video_url)
        hook_text = None

        try:
            hook_text = self.hook_extraction(video_url)
        except Exception:
            hook_text = transcript_data["transcript"][:500]

        return {
            "metadata": metadata,
            "transcript_source": transcript_data["source"],
            "transcript": transcript_data["transcript"],
            "hook_text": hook_text
        }


if __name__ == "__main__":

    VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    extractor = YouTubeExtractor()

    result = extractor.extract(VIDEO_URL)

    print("\nTITLE:")
    print(result["metadata"]["title"])

    print("\nTRANSCRIPT SOURCE:")
    print(result["transcript_source"])

    print("\nTRANSCRIPT PREVIEW:")
    print(result["transcript"][:1000])
