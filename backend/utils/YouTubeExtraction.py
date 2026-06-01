import os
import re
import tempfile

import yt_dlp
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeExtractor:

    def __init__(self, groq_api_key=None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.enable_whisper_fallback = (
            os.getenv("ENABLE_WHISPER_FALLBACK", "false").lower()
            == "true"
        )

        self.client = None
        if self.groq_api_key and self.enable_whisper_fallback:
            self.client = Groq(api_key=self.groq_api_key)

    @staticmethod
    def get_ytdlp_options(extra_options: dict | None = None) -> dict:
        cookie_file = YouTubeExtractor.get_ytdlp_cookie_file()

        options = {
            "quiet": True,
            "retries": 3,
            "extractor_retries": 3,
            "socket_timeout": 20,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                )
            }
        }

        if cookie_file:
            options["cookiefile"] = cookie_file

        if extra_options:
            options.update(extra_options)

        return options

    @staticmethod
    def get_ytdlp_cookie_file() -> str | None:
        cookie_file = os.getenv("YOUTUBE_COOKIES_FILE")

        if cookie_file:
            cookie_path = os.path.join(
                tempfile.gettempdir(),
                "youtube_cookies.txt"
            )

            with open(
                cookie_file,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as source_cookie_file:
                cookie_content = source_cookie_file.read()

            with open(
                cookie_path,
                "w",
                encoding="utf-8"
            ) as runtime_cookie_file:
                runtime_cookie_file.write(cookie_content)

            return cookie_path

        cookie_content = os.getenv("YOUTUBE_COOKIES_CONTENT")

        if not cookie_content:
            return None

        cookie_path = os.path.join(
            tempfile.gettempdir(),
            "youtube_cookies.txt"
        )
        normalized_cookie_content = cookie_content.replace("\\n", "\n")

        with open(
            cookie_path,
            "w",
            encoding="utf-8"
        ) as cookie_handle:
            cookie_handle.write(normalized_cookie_content)

        return cookie_path

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

        ydl_opts = YouTubeExtractor.get_ytdlp_options({
            "skip_download": True,
            "extract_flat": False,
            "noplaylist": True,
            "ignore_no_formats_error": True,
        })

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
    # YT-DLP AUTO SUBTITLE FALLBACK
    # ============================================================

    @staticmethod
    def clean_subtitle_text(subtitle_text: str) -> str:

        subtitle_text = re.sub(
            r"WEBVTT.*?Kind: captions",
            "",
            subtitle_text,
            flags=re.DOTALL
        )
        subtitle_text = re.sub(
            r"\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}.*",
            "",
            subtitle_text
        )
        subtitle_text = re.sub(
            r"<[^>]+>",
            "",
            subtitle_text
        )
        subtitle_text = re.sub(
            r"^\s*(align|position):.*$",
            "",
            subtitle_text,
            flags=re.MULTILINE
        )

        lines = [
            line.strip()
            for line in subtitle_text.splitlines()
            if line.strip()
        ]

        deduped_lines = []
        previous_line = None

        for line in lines:
            if line != previous_line:
                deduped_lines.append(line)
            previous_line = line

        return " ".join(deduped_lines).strip()

    @staticmethod
    def subtitle_file_to_text(subtitle_path: str) -> str:

        with open(
            subtitle_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as subtitle_file:
            subtitle_text = subtitle_file.read()

        return YouTubeExtractor.clean_subtitle_text(subtitle_text)

    @staticmethod
    def subtitle_extraction(video_url: str) -> str:

        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(
                temp_dir,
                "%(id)s.%(ext)s"
            )

            ydl_opts = YouTubeExtractor.get_ytdlp_options({
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
                "subtitlesformat": "vtt",
                "outtmpl": output_template,
                "ignore_no_formats_error": True,
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

            subtitle_paths = [
                os.path.join(temp_dir, file_name)
                for file_name in os.listdir(temp_dir)
                if file_name.endswith(".vtt")
            ]

            if not subtitle_paths:
                raise ValueError("No English subtitles found with yt-dlp.")

            subtitle_text = YouTubeExtractor.subtitle_file_to_text(
                subtitle_paths[0]
            )

            if not subtitle_text:
                raise ValueError("Downloaded subtitles were empty.")

            return subtitle_text

    # ============================================================
    # FALLBACK STARTS -----  AUDIO DOWNLOAD
    # ============================================================

    @staticmethod
    def download_audio(video_url: str, temp_dir: str) -> str:

        output_template = os.path.join(
            temp_dir,
            "%(id)s.%(ext)s"
        )

        ydl_opts = YouTubeExtractor.get_ytdlp_options({
            "outtmpl": output_template,
            "noplaylist": True,
            "format": "bestaudio/best",
        })

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
                f"Trying yt-dlp auto subtitles.\n"
                f"Reason: {transcript_error}"
            )

            try:
                transcript = self.subtitle_extraction(video_url)

                return {
                    "source": "yt_dlp_auto_subtitles",
                    "transcript": transcript
                }
            except Exception as subtitle_error:
                print(
                    "yt-dlp subtitles failed. "
                    f"Whisper fallback enabled: {self.enable_whisper_fallback}.\n"
                    f"Reason: {subtitle_error}"
                )

            if not self.enable_whisper_fallback:
                raise RuntimeError(
                    "YouTube transcript API and yt-dlp subtitles failed. "
                    "Whisper fallback is disabled."
                ) from transcript_error

            if not self.client:
                raise RuntimeError(
                    "Transcript API failed and "
                    "Groq client is unavailable."
                ) from transcript_error

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
        transcript_data = {
            "source": None,
            "transcript": None
        }

        try:
            transcript_data = self.get_transcript(video_url)
        except Exception as transcript_error:
            print(
                "YouTube transcript unavailable. "
                f"Continuing with metadata only. Reason: {transcript_error}"
            )

        hook_text = None

        try:
            hook_text = self.hook_extraction(video_url)
        except Exception:
            transcript = transcript_data.get("transcript") or ""
            hook_text = transcript[:500] or None

        return {
            "metadata": metadata,
            "transcript_source": transcript_data.get("source"),
            "transcript": transcript_data.get("transcript"),
            "hook_text": hook_text,
            "transcript_available": bool(transcript_data.get("transcript"))
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
