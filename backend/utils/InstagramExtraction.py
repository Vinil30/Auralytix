import os
import tempfile
from datetime import datetime

import instaloader
from groq import Groq
import yt_dlp


class InstagramExtractor:

    def __init__(self, groq_api_key=None):

        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True
        )

        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")

        self.client = None
        if self.groq_api_key:
            self.client = Groq(api_key=self.groq_api_key)

    # ============================================================
    # SHORTCODE EXTRACTION
    # ============================================================

    @staticmethod
    def extract_shortcode(url: str) -> str:

        parts = url.strip("/").split("/")

        if "reel" in parts:
            return parts[parts.index("reel") + 1]

        if "p" in parts:
            return parts[parts.index("p") + 1]

        raise ValueError("Unable to extract Instagram shortcode.")

    # ============================================================
    # POST OBJECT
    # ============================================================

    def get_post(self, instagram_url):

        shortcode = self.extract_shortcode(instagram_url)

        return instaloader.Post.from_shortcode(
            self.loader.context,
            shortcode
        )

    # ============================================================
    # METADATA EXTRACTION
    # ============================================================

    def metadata_extraction(self, instagram_url):

        post = self.get_post(instagram_url)

        views = getattr(post, "video_view_count", None)

        likes = post.likes or 0
        comments = post.comments or 0

        engagement_rate = None

        if views and views > 0:
            engagement_rate = round(
                ((likes + comments) / views) * 100,
                2
            )

        return {
            "platform": "instagram",
            "shortcode": post.shortcode,
            "post_id": post.mediaid,
            "caption": post.caption,
            "hashtags": post.caption_hashtags,
            "mentions": post.caption_mentions,
            "owner_username": post.owner_username,
            "owner_id": post.owner_id,
            "likes": likes,
            "comments": comments,
            "views": views,
            "engagement_rate": engagement_rate,
            "is_video": post.is_video,
            "video_duration": getattr(
                post,
                "video_duration",
                None
            ),
            "upload_date": post.date_utc.isoformat(),
            "url": instagram_url
        }

    # ============================================================
    # VIDEO DOWNLOAD
    # ============================================================

    @staticmethod
    def download_video(instagram_url, temp_dir):

        output_template = os.path.join(
            temp_dir,
            "%(id)s.%(ext)s"
        )

        ydl_opts = {
            "quiet": True,
            "outtmpl": output_template,
            "format": "best"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                instagram_url,
                download=True
            )

            return ydl.prepare_filename(info)

    # ============================================================
    # WHISPER TRANSCRIPTION
    # ============================================================

    def whisper_transcription(self, video_path):

        if not self.client:
            raise ValueError(
                "GROQ_API_KEY not configured."
            )

        with open(video_path, "rb") as media_file:

            response = self.client.audio.transcriptions.create(
                file=media_file,
                model="whisper-large-v3"
            )

        return response.text

    # ============================================================
    # OPTIONAL TRANSCRIPT
    # ============================================================

    def transcript_extraction(self, instagram_url):

        if not self.client:
            raise ValueError(
                "Transcript requested but "
                "Groq client unavailable."
            )

        with tempfile.TemporaryDirectory() as temp_dir:

            video_path = self.download_video(
                instagram_url,
                temp_dir
            )

            transcript = self.whisper_transcription(
                video_path
            )

            return transcript

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract(
        self,
        instagram_url,
        generate_transcript=False
    ):

        metadata = self.metadata_extraction(
            instagram_url
        )

        result = {
            "metadata": metadata,
            "transcript": None,
            "transcript_available": False
        }

        if generate_transcript:

            transcript = self.transcript_extraction(
                instagram_url
            )

            result["transcript"] = transcript
            result["transcript_available"] = True

        return result



if __name__ == "__main__":

    URL = "https://www.instagram.com/reel/XXXXXXXXXXX/"

    extractor = InstagramExtractor()

    # Fast Mode
    result = extractor.extract(
        URL,
        generate_transcript=False
    )

    print(result["metadata"])

    # Deep Mode
    # result = extractor.extract(
    #     URL,
    #     generate_transcript=True
    # )