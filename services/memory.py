import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional


class MemoryStore:
    """File-backed per-session memory store with in-memory cache."""

    def __init__(self, base_dir: str = "data/sessions") -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        # cache maps session_id -> {"messages": List[dict], "summary": str}
        self._cache: Dict[str, dict] = {}

    def _session_path(self, session_id: str) -> Path:
        return self.base_path / f"{session_id}.json"

    def get_messages(self, session_id: str) -> List[dict]:
        with self._lock:
            if session_id in self._cache:
                return list(self._cache[session_id].get("messages", []))
            path = self._session_path(session_id)
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        # legacy format
                        self._cache[session_id] = {"messages": data, "summary": ""}
                        return list(data)
                    elif isinstance(data, dict):
                        messages = data.get("messages", [])
                        summary = data.get("summary", "")
                        self._cache[session_id] = {"messages": messages, "summary": summary}
                        return list(messages)
                except Exception:
                    return []
            self._cache[session_id] = {"messages": [], "summary": ""}
            return []

    def append_message(self, session_id: str, message: dict) -> None:
        with self._lock:
            entry = self._cache.get(session_id, {"messages": [], "summary": ""})
            msgs = entry.get("messages", [])
            msgs.append(message)
            # Limit to last 100
            if len(msgs) > 100:
                msgs = msgs[-80:]
            entry["messages"] = msgs
            self._cache[session_id] = entry
            # Persist
            self._session_path(session_id).write_text(
                json.dumps({"messages": msgs, "summary": entry.get("summary", "")}, ensure_ascii=False),
                encoding="utf-8",
            )

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._cache.pop(session_id, None)
            path = self._session_path(session_id)
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass

    def get_recent_messages(self, session_id: str, limit: int = 20) -> List[dict]:
        msgs = self.get_messages(session_id)
        return msgs[-limit:] if len(msgs) > limit else msgs

    def error_summary(self, session_id: str) -> Dict[str, int]:
        errors: Dict[str, int] = {}
        for m in self.get_messages(session_id):
            et = m.get("error_type")
            if et:
                errors[et] = errors.get(et, 0) + 1
        return errors

    def sessions(self) -> List[str]:
        with self._lock:
            ids = set(self._cache.keys())
            for p in self.base_path.glob("*.json"):
                ids.add(p.stem)
            return sorted(list(ids))

    def stats(self) -> Dict[str, dict]:
        data: Dict[str, dict] = {}
        for sid in self.sessions():
            msgs = self.get_messages(sid)
            last_ts = max((m.get("timestamp", 0) for m in msgs), default=0)
            error_count = sum(1 for m in msgs if m.get("error_type"))
            data[sid] = {
                "session_id": sid,
                "message_count": len(msgs),
                "last_activity": last_ts,
                "error_count": error_count,
            }
        return data

    def total_messages(self) -> int:
        return sum(v.get("message_count", 0) for v in self.stats().values())

    # Summary APIs
    def get_summary(self, session_id: str) -> str:
        with self._lock:
            # ensure entry is loaded
            _ = self.get_messages(session_id)
            return self._cache.get(session_id, {}).get("summary", "") or ""

    def set_summary(self, session_id: str, summary: str) -> None:
        with self._lock:
            # ensure entry is loaded
            _ = self.get_messages(session_id)
            entry = self._cache.get(session_id, {"messages": [], "summary": ""})
            entry["summary"] = summary
            self._cache[session_id] = entry
            self._session_path(session_id).write_text(
                json.dumps({"messages": entry.get("messages", []), "summary": summary}, ensure_ascii=False),
                encoding="utf-8",
            )


