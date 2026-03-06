from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Iterable

from .models import ContentRecord

CONTENT_METHOD_CANDIDATES: dict[str, tuple[str, ...]] = {
    "articles": ("get_posts", "posts", "list_posts", "fetch_posts"),
    "notes": ("get_notes", "notes", "list_notes", "fetch_notes"),
    "podcasts": ("get_podcasts", "podcasts", "list_podcasts", "fetch_podcasts"),
    "events": ("get_events", "events", "list_events", "fetch_events"),
    "videos": ("get_videos", "videos", "list_videos", "fetch_videos"),
}

COMMENT_METHOD_CANDIDATES = ("get_comments", "comments", "list_comments", "fetch_comments")
TRANSCRIPT_KEYS = ("transcript", "podcast_transcript", "video_transcript")


class SubstackIngestor:
    """Adapter around `substack_api` with loose method discovery for compatibility."""

    def __init__(self, publication_url: str, cookies_path: str) -> None:
        self.publication_url = publication_url
        self.cookies_path = Path(cookies_path)
        self.client = self._build_client()

    def _build_client(self) -> Any:
        try:
            import substack_api  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "`substack_api` is required. Install it first: `pip install substack-api` or from GitHub."
            ) from exc

        cookies = json.loads(self.cookies_path.read_text(encoding="utf-8"))

        for attr in ("SubstackApi", "Substack", "Client"):
            cls = getattr(substack_api, attr, None)
            if cls is None:
                continue
            kwargs = {"publication": self.publication_url, "cookies": cookies}
            try:
                return cls(**kwargs)
            except TypeError:
                kwargs = {"pub": self.publication_url, "cookies": cookies}
                try:
                    return cls(**kwargs)
                except TypeError:
                    continue

        raise RuntimeError("Could not initialize substack_api client. Unsupported constructor signature.")

    def fetch_all_content(self) -> list[ContentRecord]:
        records: list[ContentRecord] = []
        for content_type, method_names in CONTENT_METHOD_CANDIDATES.items():
            data_items = self._call_first_existing(method_names)
            for item in self._iter_items(data_items):
                if not isinstance(item, dict):
                    continue
                comments = self._fetch_comments(item)
                record = ContentRecord(
                    record_id=str(item.get("id") or item.get("post_id") or item.get("slug") or item.get("canonical_url")),
                    content_type=content_type,
                    title=str(item.get("title") or item.get("headline") or "Untitled"),
                    body=str(item.get("body") or item.get("description") or item.get("content") or ""),
                    url=str(item.get("canonical_url") or item.get("url") or ""),
                    published_at=item.get("post_date") or item.get("published_at") or item.get("date"),
                    transcript=self._extract_transcript(item),
                    comments=comments,
                    metadata={"raw_type": item.get("type"), "slug": item.get("slug")},
                )
                records.append(record)
        return records

    def _extract_transcript(self, item: dict[str, Any]) -> str | None:
        for key in TRANSCRIPT_KEYS:
            if item.get(key):
                return str(item[key])
        media_obj = item.get("media")
        if isinstance(media_obj, dict):
            for key in TRANSCRIPT_KEYS:
                if media_obj.get(key):
                    return str(media_obj[key])
        return None

    def _fetch_comments(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        identifier = item.get("id") or item.get("post_id") or item.get("slug")
        if identifier is None:
            return []

        method = self._resolve_method(COMMENT_METHOD_CANDIDATES)
        if method is None:
            return []

        try:
            payload = self._call_with_best_effort(method, identifier)
        except Exception:
            return []

        comments: list[dict[str, Any]] = []
        for comment in self._iter_items(payload):
            if isinstance(comment, dict):
                comments.append(comment)
        return comments

    def _call_first_existing(self, candidates: Iterable[str]) -> Any:
        method = self._resolve_method(candidates)
        if method is None:
            return []
        return self._call_with_best_effort(method)

    def _resolve_method(self, candidates: Iterable[str]) -> Any | None:
        for name in candidates:
            method = getattr(self.client, name, None)
            if callable(method):
                return method
        return None

    @staticmethod
    def _iter_items(payload: Any) -> Iterable[Any]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("items", "results", "posts", "notes", "data"):
                maybe = payload.get(key)
                if isinstance(maybe, list):
                    return maybe
        return []

    @staticmethod
    def _call_with_best_effort(method: Any, *args: Any) -> Any:
        sig = inspect.signature(method)
        required = [
            p
            for p in sig.parameters.values()
            if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        if len(args) >= len(required):
            return method(*args)
        if len(required) == 0:
            return method()
        if len(required) == 1 and args:
            return method(args[0])
        raise TypeError(f"Cannot call {method.__name__}: incompatible signature")
