from __future__ import annotations

import argparse
from typing import Any

from .haiku_rag import HaikuRAGClient, HaikuRAGConfig
from .substack_source import SubstackIngestor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="substack-agent",
        description="Ingest a subscribed Substack into a Haiku RAG collection backed by LM Studio.",
    )
    parser.add_argument("--pub", required=True, help="Substack publication URL, e.g. https://foo.substack.com")
    parser.add_argument("--cookies", required=True, help="Path to cookies JSON exported from browser")
    parser.add_argument("--haiku-url", default="http://127.0.0.1:8000", help="haiku.rag server URL")
    parser.add_argument("--lmstudio-url", default="http://127.0.0.1:1234/v1", help="LM Studio OpenAI API URL")
    parser.add_argument("--embedding-model", default="text-embedding-nomic-embed-text-v1.5")
    parser.add_argument("--chat-model", default="local-model")
    parser.add_argument("--collection", default="substack")
    parser.add_argument("--top-k", type=int, default=8)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    print("Fetching Substack content (articles, notes, podcasts, events, videos + comments)...")
    ingestor = SubstackIngestor(publication_url=args.pub, cookies_path=args.cookies)
    records = ingestor.fetch_all_content()
    print(f"Fetched {len(records)} records.")

    rag = HaikuRAGClient(
        HaikuRAGConfig(
            base_url=args.haiku_url,
            collection=args.collection,
            lm_studio_base_url=args.lmstudio_url,
            embedding_model=args.embedding_model,
            chat_model=args.chat_model,
        )
    )

    print("Creating/using collection in haiku.rag and indexing content...")
    rag.ensure_collection()
    rag.index_records(records)
    print("Indexing complete.")

    print("Interactive chat ready. Type 'exit' to quit.")
    while True:
        question = input("\nYou> ").strip()
        if question.lower() in {"exit", "quit", ":q"}:
            break
        if not question:
            continue

        answer = rag.query(question, top_k=args.top_k)
        _render_answer(answer)

    return 0


def _render_answer(answer: dict[str, Any]) -> None:
    reply = answer.get("answer") or answer.get("response") or "(No answer text in response payload)"
    print(f"\nAssistant> {reply}")
    sources = answer.get("sources") or answer.get("citations") or []
    if isinstance(sources, list) and sources:
        print("Sources:")
        for idx, source in enumerate(sources, start=1):
            if isinstance(source, dict):
                title = source.get("title") or source.get("id") or "source"
                url = source.get("url") or source.get("metadata", {}).get("url") or ""
                print(f"  {idx}. {title} {url}".rstrip())
            else:
                print(f"  {idx}. {source}")


def main() -> None:
    args = parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
