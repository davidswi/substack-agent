from substack_agent.models import ContentRecord


def test_to_rag_text_includes_transcript_and_comments() -> None:
    record = ContentRecord(
        record_id="1",
        content_type="podcasts",
        title="Episode 1",
        body="Main body",
        url="https://example.com/1",
        transcript="Full transcript",
        comments=[{"author": "alice", "body": "Great post"}],
    )

    output = record.to_rag_text()

    assert "Transcript:" in output
    assert "Full transcript" in output
    assert "alice: Great post" in output


def test_rag_metadata_base_fields() -> None:
    record = ContentRecord(
        record_id="x",
        content_type="articles",
        title="T",
        body="B",
        url="U",
        comments=[{"author": "a"}],
        metadata={"slug": "foo"},
    )

    meta = record.rag_metadata()

    assert meta["record_id"] == "x"
    assert meta["comment_count"] == 1
    assert meta["slug"] == "foo"
