from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ContentRecord:
    record_id: str
    content_type: str
    title: str
    body: str
    url: str
    published_at: str | None = None
    transcript: str | None = None
    comments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_rag_text(self) -> str:
        lines = [
            f"Type: {self.content_type}",
            f"Title: {self.title}",
            f"URL: {self.url}",
            f"Published At: {self.published_at or 'unknown'}",
            "",
            self.body.strip(),
        ]
        if self.transcript:
            lines.extend(["", "Transcript:", self.transcript.strip()])
        if self.comments:
            lines.append("\nComments:")
            for comment in self.comments:
                author = comment.get("author") or comment.get("name") or "unknown"
                text = comment.get("body") or comment.get("text") or ""
                lines.append(f"- {author}: {text}".strip())
        return "\n".join(lines).strip()

    def rag_metadata(self) -> dict[str, Any]:
        base = {
            "record_id": self.record_id,
            "type": self.content_type,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "comment_count": len(self.comments),
            "has_transcript": bool(self.transcript),
        }
        return {**base, **self.metadata}
