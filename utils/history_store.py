from __future__ import annotations

import contextlib
import json
import os
import tempfile
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
            root = Path(xdg_state) / "streamnest" if xdg_state else Path.home() / ".local" / "state" / "streamnest"
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
        entries: list[HistoryEntry] = [
            HistoryEntry.from_dict(item) for item in raw_entries if isinstance(item, dict)
        ]
        return entries[:50]

    def save(self, entries: list[HistoryEntry]) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            cipher = Fernet(self._get_or_create_key())
            payload = json.dumps([entry.to_dict() for entry in entries[:50]], ensure_ascii=True).encode("utf-8")
            encrypted = cipher.encrypt(payload)
            self._atomic_write_bytes(self._data_file, encrypted)
        except OSError:
            fallback = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest"
            fallback.mkdir(parents=True, exist_ok=True)
            fallback_key = fallback / ".history.key"
            cipher = Fernet(self._get_or_create_key(key_file=fallback_key))
            payload = json.dumps([entry.to_dict() for entry in entries[:50]], ensure_ascii=True).encode("utf-8")
            encrypted = cipher.encrypt(payload)
            self._atomic_write_bytes(fallback / "download_history.enc", encrypted)

    def clear(self) -> None:
        try:
            self.save([])
        except OSError:
            fallback = Path(os.getenv("TMPDIR", "/tmp")) / "streamnest"
            fallback.mkdir(parents=True, exist_ok=True)
            cipher = Fernet(self._get_or_create_key())
            self._atomic_write_bytes(fallback / "download_history.enc", cipher.encrypt(b"[]"))

    def _atomic_write_bytes(self, path: Path, data: bytes) -> None:
        """Write bytes to ``path`` atomically via a temp file in the same directory."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_history_")
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(data)
            Path(tmp_name).replace(path)
        except Exception:
            with contextlib.suppress(OSError):
                Path(tmp_name).unlink()
            raise

    def _get_or_create_key(self, key_file: Path | None = None) -> bytes:
        target_key_file = key_file or self._key_file
        env_key = os.getenv("STREAMNEST_HISTORY_KEY")
        if env_key:
            return env_key.encode("utf-8")

        if target_key_file.exists():
            try:
                key = target_key_file.read_bytes().strip()
                if key:
                    self._enforce_key_permissions(target_key_file)
                    return key
            except OSError:
                pass

        key = Fernet.generate_key()
        try:
            target_key_file.parent.mkdir(parents=True, exist_ok=True)
            target_key_file.write_bytes(key)
            self._enforce_key_permissions(target_key_file)
        except OSError:
            pass
        return key

    @staticmethod
    def _enforce_key_permissions(key_file: Path) -> None:
        """Ensure the key file is readable only by the owner (0o600)."""
        try:
            current_mode = key_file.stat().st_mode & 0o777
            if current_mode != 0o600:
                key_file.chmod(0o600)
        except OSError:
            pass
