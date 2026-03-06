from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request
from urllib.error import HTTPError

from .models import ContentRecord


@dataclass(slots=True)
class HaikuRAGConfig:
    base_url: str = "http://127.0.0.1:8000"
    collection: str = "substack"
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    chat_model: str = "local-model"


class HaikuRAGClient:
    """HTTP adapter for a running haiku.rag service configured to use LM Studio."""

    def __init__(self, config: HaikuRAGConfig) -> None:
        self.config = config

    def ensure_collection(self) -> None:
        payload = {
            "name": self.config.collection,
            "provider": {
                "type": "lmstudio",
                "base_url": self.config.lm_studio_base_url,
                "embedding_model": self.config.embedding_model,
                "chat_model": self.config.chat_model,
            },
        }
        self._post("/collections", payload, allow_conflict=True)

    def index_records(self, records: list[ContentRecord]) -> None:
        for record in records:
            payload = {
                "id": record.record_id,
                "text": record.to_rag_text(),
                "metadata": record.rag_metadata(),
            }
            self._post(f"/collections/{self.config.collection}/documents", payload)

    def query(self, question: str, top_k: int = 8) -> dict[str, Any]:
        payload = {"question": question, "top_k": top_k}
        return self._post(f"/collections/{self.config.collection}/chat", payload)

    def _post(self, path: str, payload: dict[str, Any], allow_conflict: bool = False) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with request.urlopen(req, timeout=60) as resp:  # nosec B310
                body = resp.read().decode("utf-8").strip()
                return json.loads(body) if body else {}
        except HTTPError as exc:
            if allow_conflict and exc.code == 409:
                return {}
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"haiku.rag error {exc.code}: {body}") from exc
