# legalchat/memory/session_memory.py

from collections import deque
from threading import Lock
from typing import Dict, List, Optional


class SessionMemory:
    """
    Stores short-term semantic memory per session.
    This memory is:
    - NOT raw chat
    - NOT verdict-affecting
    - ONLY semantic context
    """

    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self._store: Dict[str, deque] = {}
        self._lock = Lock()

    def add_turn(self, session_id: str, semantic_data: Dict):
        """
        semantic_data example:
        {
            "verdict_type": "legal",
            "legal_domain": "contract_clause",
            "statute_names": ["Indian Contract Act, 1872"],
            "section_numbers": ["73", "74"],
            "primary_doctrine": "Indian Contract Act, Section 27"
        }
        STRICTLY NO RAW TEXT OR SUMMARIES.
        """
        if not session_id or not semantic_data:
            return

        # Hard filter to ensure no raw text leaks in
        clean_data = {
            "verdict_type": semantic_data.get("verdict_type"),
            "legal_domain": semantic_data.get("legal_domain"),
            "statute_names": semantic_data.get("statute_names"),
            "section_numbers": semantic_data.get("section_numbers"),
            "primary_doctrine": semantic_data.get("primary_doctrine")
        }

        # Remove None values and empty lists
        clean_data = {k: v for k, v in clean_data.items() if v}

        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self.max_turns)

            self._store[session_id].append(clean_data)

    def get_context(self, session_id: str) -> List[Dict]:
        """
        Returns last semantic states for the session.
        Used ONLY for context building, never directly for verdict.
        """
        if not session_id:
            return []

        with self._lock:
            return list(self._store.get(session_id, []))

    def clear(self, session_id: str):
        """Clear session memory (optional use on chat end)."""
        if not session_id:
            return

        with self._lock:
            if session_id in self._store:
                del self._store[session_id]

    def has_session(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._store
