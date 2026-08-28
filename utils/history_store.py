from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from state.app_state import HistoryEntry


class HistoryStore:
    """Encrypted local storage for download history."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is not None:
            root = base_dir
        else:
            xdg_state = os.getenv("XDG_STATE_HOME")
            if xdg_state:
                root = Path(xdg_state) / "streamnest"
            else:
                root = Path.home() / ".local" / "state" / "streamnest"
        self._root = root
        self._key_file = root / ".history.key"
        self._data_file = root / "download_history.enc"

    def load(self) -> list[HistoryEntry]:
        try:
            return self._load_from(self._data_file, self._key_file)
        except (InvalidToken, OSError, ValueError, json.JSONDecodeError):
            pass

        fallback_data = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest" / "download_history.enc"
        if not fallback_data.exists():
            return []
        try:
            fallback_key = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest" / ".history.key"
            return self._load_from(fallback_data, fallback_key)
        except (InvalidToken, OSError, ValueError, json.JSONDecodeError):
            return []

    def _load_from(self, data_file: Path, key_file: Path) -> list[HistoryEntry]:
        encrypted = data_file.read_bytes()
        if not encrypted:
            return []
        cipher = Fernet(self._get_or_create_key(key_file=key_file))
        payload = cipher.decrypt(encrypted)
        raw_entries = json.loads(payload.decode("utf-8"))
        if not isinstance(raw_entries, list):
            return []
        entries: list[HistoryEntry] = []
        for item in raw_entries:
            if isinstance(item, dict):
                entries.append(HistoryEntry.from_dict(item))
        return entries[:50]

    def save(self, entries: list[HistoryEntry]) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            cipher = Fernet(self._get_or_create_key())
            payload = json.dumps([entry.to_dict() for entry in entries[:50]], ensure_ascii=True).encode("utf-8")
            encrypted = cipher.encrypt(payload)
            self._data_file.write_bytes(encrypted)
        except OSError:
            fallback = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest"
            fallback.mkdir(parents=True, exist_ok=True)
            fallback_key = fallback / ".history.key"
            cipher = Fernet(self._get_or_create_key(key_file=fallback_key))
            payload = json.dumps([entry.to_dict() for entry in entries[:50]], ensure_ascii=True).encode("utf-8")
            encrypted = cipher.encrypt(payload)
            Path(fallback / "download_history.enc").write_bytes(encrypted)

    def clear(self) -> None:
        try:
            self.save([])
        except OSError:
            fallback = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest"
            fallback.mkdir(parents=True, exist_ok=True)
            cipher = Fernet(self._get_or_create_key())
            cipher.encrypt(b"[]")
            Path(fallback / "download_history.enc").write_bytes(cipher.encrypt(b"[]"))

    def _get_or_create_key(self, key_file: Path | None = None) -> bytes:
        target_key_file = key_file or self._key_file
        env_key = os.getenv("STREAMNEST_HISTORY_KEY")
        if env_key:
            return env_key.encode("utf-8")

        if target_key_file.exists():
            try:
                key = target_key_file.read_bytes().strip()
                if key:
                    return key
            except OSError:
                pass

        key = Fernet.generate_key()
        try:
            target_key_file.parent.mkdir(parents=True, exist_ok=True)
            target_key_file.write_bytes(key)
            os.chmod(target_key_file, 0o600)
        except OSError:
            pass
        return key
