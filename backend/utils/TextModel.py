import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class TextModel:

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
        video_b_data: dict
    ) -> str:

        system_prompt = """
                    You are an expert social media content analyst.

                    Compare two pieces of content.
                    Focus on:
                    1. Content themes
                    2. Audience targeting
                    3. Engagement metrics
                    4. Similarities
                    5. Differences
                    6. Strengths
                    7. Improvement opportunities

                    Provide a structured comparison.
                    """

        user_prompt = f"""
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

            Answer the user's question accurately.
            If information is unavailable,
            clearly mention that.
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

    def answer_question_with_rag(self,question: str,session_context: dict,retrieved_context: str) -> str:

        system_prompt = """
            You are a social media analysis assistant.

            Use:
            1. Session context first.
            2. Retrieved knowledge if relevant.

            Do not invent facts.
            """

        user_prompt = f"""
            SESSION CONTEXT
            {session_context}
            RETRIEVED CONTEXT
            {retrieved_context}
            QUESTION
            {question}
            """

        return self.generate(system_prompt,user_prompt)