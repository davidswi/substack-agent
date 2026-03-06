# substack-agent

`substack-agent` ingests content from a Substack you subscribe to (using `substack_api`) and pushes it into a `haiku.rag` collection configured for LM Studio embeddings/chat.

## Features

- Ingests publication content by type:
  - articles
  - notes
  - podcasts
  - events
  - videos
- Includes transcripts when available (podcasts/videos).
- Includes comments for each piece of content.
- Indexes all fetched records into a `haiku.rag` collection.
- Opens an interactive CLI chat loop for querying the indexed knowledge base.

## Install

```bash
pip install -e .
# plus substack_api from GitHub
pip install git+https://github.com/NHagar/substack_api.git
```

You also need a running `haiku.rag` server and LM Studio server.

## Usage

```bash
substack-agent \
  --pub https://foo.substack.com \
  --cookies cookies.json \
  --haiku-url http://127.0.0.1:8000 \
  --lmstudio-url http://127.0.0.1:1234/v1
```

### Required arguments

- `--pub`: publication URL.
- `--cookies`: path to cookie JSON exported from your browser session.

### Optional arguments

- `--collection`: target RAG collection (default `substack`).
- `--embedding-model`: LM Studio embedding model name.
- `--chat-model`: LM Studio chat model name.
- `--top-k`: number of chunks/documents retrieved per query.

## Notes on API compatibility

Both `substack_api` and `haiku.rag` are evolving quickly. This project uses method/endpoint adapters designed to be resilient across minor naming differences. If your versions expose different method names or routes, update:

- `substack_agent/substack_source.py` for extraction adapters.
- `substack_agent/haiku_rag.py` for haiku.rag endpoint mapping.
