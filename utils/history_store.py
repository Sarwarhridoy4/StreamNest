from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from state.app_state import HistoryEntry


class HistoryStore:
    """Encrypted local storage for download history."""

    def __init__(self, base_dir: Path | None = None) -> None:
        root = base_dir or Path(__file__).resolve().parent.parent / "state"
        self._root = root
        self._key_file = root / ".history.key"
        self._data_file = root / "download_history.enc"

    def load(self) -> list[HistoryEntry]:
        if not self._data_file.exists():
            return []
        try:
            encrypted = self._data_file.read_bytes()
            if not encrypted:
                return []
            cipher = Fernet(self._get_or_create_key())
            payload = cipher.decrypt(encrypted)
            raw_entries = json.loads(payload.decode("utf-8"))
            if not isinstance(raw_entries, list):
                return []
            entries: list[HistoryEntry] = []
            for item in raw_entries:
                if isinstance(item, dict):
                    entries.append(HistoryEntry.from_dict(item))
            return entries[:50]
        except (InvalidToken, OSError, ValueError, json.JSONDecodeError):
            return []

    def save(self, entries: list[HistoryEntry]) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        cipher = Fernet(self._get_or_create_key())
        payload = json.dumps([entry.to_dict() for entry in entries[:50]], ensure_ascii=True).encode("utf-8")
        encrypted = cipher.encrypt(payload)
        self._data_file.write_bytes(encrypted)

    def clear(self) -> None:
        self.save([])

    def _get_or_create_key(self) -> bytes:
        env_key = os.getenv("STREAMNEST_HISTORY_KEY")
        if env_key:
            return env_key.encode("utf-8")

        self._root.mkdir(parents=True, exist_ok=True)
        if self._key_file.exists():
            key = self._key_file.read_bytes().strip()
            if key:
                return key

        key = Fernet.generate_key()
        self._key_file.write_bytes(key)
        try:
            os.chmod(self._key_file, 0o600)
        except OSError:
            pass
        return key
