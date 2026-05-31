# session/session_store.py

from typing import Dict, Any
from uuid import uuid4
from datetime import datetime


class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> str:
        session_id = str(uuid4())

        self.sessions[session_id] = {
            "video_a_data": None,
            "video_b_data": None,
            "youtube_data": None,
            "instagram_data": None,
            "comparison_result": None,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        return session_id

    def get_session(self, session_id: str) -> Dict[str, Any] | None:
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs):
        if session_id not in self.sessions:
            return

        self.sessions[session_id].update(kwargs)
        self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        if session_id not in self.sessions:
            return

        self.sessions[session_id]["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


session_store = SessionStore()
