import os
import json
import re
from schemas import QueryClassification
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()


class TextModel:
    def classify_query(self, query: str) -> QueryClassification:
        query = query.strip()

        if not query:
            raise ValueError("Query cannot be empty.")

        deterministic_classification = self._classify_obvious_query(query)

        if deterministic_classification:
            return deterministic_classification

        system_prompt = """
        You are a query classification agent.

        Classify the query into one of:

        1. comparison
        - compare content
        - similarities
        - differences
        - summarize both

        2. transcript_qa
        - questions about extracted content
        - transcript analysis
        - topic analysis
        - sentiment analysis
        - creator statements

        3. recommendation
        - marketing recommendations
        - content strategy
        - posting advice
        - platform suggestions
        - video-specific improvements

        Return ONLY valid JSON.

        Examples:

        {
        "intent": "comparison",
        "use_rag": false,
        "collection_name": null
        }

        {
        "intent": "transcript_qa",
        "use_rag": true,
        "collection_name": "social_content"
        }

        {
        "intent": "recommendation",
        "use_rag": true,
        "collection_name": "social_content"
        }
        """

        response = self.generate(
            system_prompt=system_prompt,
            user_prompt=query,
            temperature=0
        )

        try:
            return self._normalize_classification(
                QueryClassification.model_validate_json(response)
            )
        except ValidationError:
            try:
                return self._normalize_classification(
                    QueryClassification.model_validate(
                        self._extract_json_object(response)
                    )
                )
            except (ValueError, ValidationError):
                return self._fallback_classification(query)

    @staticmethod
    def _normalize_classification(
        classification: QueryClassification
    ) -> QueryClassification:
        collection_aliases = {
            "video_analytics": "social_content",
            "video_metrics": "social_content",
            "video_performance": "social_content",
            "performance": "social_content",
            "analytics": "social_content",
            "metrics": "social_content",
            "video_content": "social_content",
            "transcript": "social_content",
            "transcripts": "social_content",
            "social_media": "social_content",
        }

        collection_name = classification.collection_name

        if collection_name:
            collection_name = collection_aliases.get(
                collection_name,
                collection_name
            )

        if collection_name not in (None, "social_content", "knowledge_base"):
            collection_name = "social_content"

        return QueryClassification(
            intent=classification.intent,
            use_rag=classification.use_rag,
            collection_name=collection_name
        )

    @staticmethod
    def _classify_obvious_query(query: str) -> QueryClassification | None:
        normalized_query = query.lower()

        metric_terms = (
            "view count",
            "views",
            "like count",
            "likes",
            "comment count",
            "comments",
            "metrics",
            "engagement",
            "duration",
            "upload date",
            "channel",
            "creator"
        )

        comparison_terms = (
            "compare",
            "comparison",
            "difference",
            "differences",
            "similar",
            "similarities",
            "versus",
            " vs ",
            "better",
            "performs better",
            "perform better",
            "winner",
            "wins"
        )

        recommendation_terms = (
            "recommend",
            "recommendation",
            "strategy",
            "improve",
            "improvement",
            "advice",
            "suggest",
            "suggestion",
            "should i",
            "what should"
        )

        if any(term in normalized_query for term in metric_terms):
            return QueryClassification(
                intent="transcript_qa",
                use_rag=False,
                collection_name=None
            )

        if any(term in normalized_query for term in comparison_terms):
            return QueryClassification(
                intent="comparison",
                use_rag=False,
                collection_name=None
            )

        if any(term in normalized_query for term in recommendation_terms):
            return QueryClassification(
                intent="recommendation",
                use_rag=True,
                collection_name="social_content"
            )

        return None

    @staticmethod
    def _extract_json_object(response: str) -> dict:
        response = response.strip()

        fenced_json = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if fenced_json:
            response = fenced_json.group(1)
        else:
            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1 or end < start:
                raise ValueError("No JSON object found in model response.")

            response = response[start:end + 1]

        return json.loads(response)

    @staticmethod
    def _fallback_classification(query: str) -> QueryClassification:
        normalized_query = query.lower()

        comparison_terms = (
            "compare",
            "comparison",
            "difference",
            "differences",
            "similar",
            "similarities",
            "versus",
            " vs ",
            "better",
            "performs better",
            "perform better",
            "winner",
            "wins"
        )

        recommendation_terms = (
            "recommend",
            "recommendation",
            "strategy",
            "improve",
            "improvement",
            "advice",
            "suggest",
            "suggestion",
            "should i",
            "what should"
        )

        if any(term in normalized_query for term in comparison_terms):
            return QueryClassification(
                intent="comparison",
                use_rag=False,
                collection_name=None
            )

        if any(term in normalized_query for term in recommendation_terms):
            return QueryClassification(
                intent="recommendation",
                use_rag=True,
                collection_name="social_content"
            )

        return QueryClassification(
            intent="transcript_qa",
            use_rag=True,
            collection_name="social_content"
        )

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        self.model = os.getenv("OPENAI_MODEL","llama-3.3-70b-versatile")

    # ============================================================
    # GENERIC GENERATION
    # ============================================================

    def generate(self,system_prompt: str,user_prompt: str,temperature: float = 0.2) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {
                    "role": "system","content": system_prompt
                },
                {
                    "role": "user","content": user_prompt
                }
            ]
        )

        return response.choices[0].message.content

    # ============================================================
    # COMPARISON
    # ============================================================

    def compare_content(
        self,
        video_a_data: dict,
        video_b_data: dict,
        question: str
    ) -> str:

        system_prompt = """
                    You are an expert social media content analyst.

                    Answer the user's specific comparison question.
                    Do not reuse a generic comparison template when the
                    user asks about one dimension such as hooks, audience,
                    engagement, performance, strengths, weaknesses, or
                    improvements.

                    Use only the supplied Video A and Video B data.
                    If the question asks about metrics or performance,
                    use the exact metric values from the data.
                    If the question asks about hooks, use hook_text first
                    before using the full transcript.
                    If the requested detail is unavailable, say it is not
                    discussed in the provided videos or any previous videos
                    available in the current context.

                    Keep the response structured, but only include sections
                    that directly answer the question.
                    """

        user_prompt = f"""
                    USER QUESTION
                    {question}

                    VIDEO A
                    {video_a_data}

                    VIDEO B
                    {video_b_data}
                    """

        return self.generate(system_prompt,user_prompt)

    # ============================================================
    # FOLLOW-UP QUESTIONS
    # ============================================================

    def answer_question(self,question: str,session_context: dict) -> str:

        system_prompt = """
            You are a social media analysis assistant.

            You have access to:
            - Previously compared content
            - Comparison results
            - User conversation context

            Answer only the user's specific question.
            If the user asks for metrics, return the exact values from
            the session context without producing a full comparison.
            If information is unavailable,
            clearly mention that it is not discussed in the provided videos
            or any previous videos available in the current context.
            """

        user_prompt = f"""
            SESSION CONTEXT
            {session_context}
            QUESTION
            {question}
            """

        return self.generate(system_prompt,user_prompt)

    # ============================================================
    # TOOL-CALLING VERSION
    # ============================================================

    def answer_question_with_rag(
        self,
        question: str,
        session_context: dict,
        retrieved_context: str,
        retrieved_sources: list[dict] | None = None
    ) -> str:

        system_prompt = """
            You are a social media analysis assistant.

            Use:
            1. Session context first.
            2. Retrieved knowledge if relevant.

            Do not invent facts.
            If the answer is unavailable, say it is not discussed in the
            provided videos or any previous videos available in the current
            context.
            Cite transcript evidence inline using the format
            [Video A chunk 0] or [Video B chunk 2] whenever you
            use retrieved transcript context.
            """

        user_prompt = f"""
            SESSION CONTEXT
            {session_context}
            RETRIEVED CONTEXT
            {retrieved_context}
            AVAILABLE SOURCES
            {retrieved_sources or []}
            QUESTION
            {question}
            """

        return self.generate(system_prompt,user_prompt)
