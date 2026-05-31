from pydantic import BaseModel, field_validator, model_validator


class ExtractRequest(BaseModel):
    video_a_url: str | None = None
    video_b_url: str | None = None
    youtube_url: str | None = None
    instagram_url: str | None = None

    @model_validator(mode="after")
    def normalize_urls(self):
        self.video_a_url = self.video_a_url or self.youtube_url
        self.video_b_url = self.video_b_url or self.instagram_url

        if not self.video_a_url or not self.video_b_url:
            raise ValueError("Two video URLs are required.")

        return self


class ChatRequest(BaseModel):
    session_id: str
    query: str

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value
