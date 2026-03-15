# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

**Prerequisites:** Python 3.13+, `uv`, Anthropic API key.

Set up `.env` in the project root:
```
ANTHROPIC_API_KEY=your-key-here
```

Install dependencies (first time):
```bash
uv sync
```

Start the server:
```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

Always use `uv` to run Python commands — never `pip` or `python` directly. For example, `uv run python script.py` instead of `python script.py`.

App runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

> On Windows, use Git Bash for these commands.

## Architecture

This is a full-stack RAG (Retrieval-Augmented Generation) chatbot. The backend is a FastAPI app (`backend/`) serving both the API and the static frontend (`frontend/`).

### Query Flow

1. **Frontend** (`frontend/script.js`) — user input triggers `POST /api/query` with `{ query, session_id }`.
2. **API layer** (`backend/app.py`) — FastAPI endpoint validates via Pydantic models, creates a session if needed, delegates to `RAGSystem`.
3. **Orchestrator** (`backend/rag_system.py`) — `RAGSystem.query()` is the central coordinator. It fetches conversation history from `SessionManager`, calls `AIGenerator` with tools, collects sources, updates history, and returns `(answer, sources)`.
4. **AI + Tool loop** (`backend/ai_generator.py`) — Calls Claude API with the `search_course_content` tool available. If Claude decides to search (`stop_reason == "tool_use"`), it executes the tool and makes a second API call with the results before returning the final answer.
5. **Vector search** (`backend/search_tools.py` + `backend/vector_store.py`) — `CourseSearchTool` calls `VectorStore.search()`, which uses ChromaDB + `all-MiniLM-L6-v2` embeddings. Course name filtering resolves fuzzy names via a semantic search against `course_catalog`, then filters `course_content` by metadata.
6. **Response** — sources and answer returned as JSON; frontend renders answer as Markdown via `marked.parse()`.

### Key Components

| File | Responsibility |
|---|---|
| `backend/app.py` | FastAPI app, routes, startup doc loading |
| `backend/rag_system.py` | Central orchestrator, wires all components |
| `backend/ai_generator.py` | Anthropic API calls, two-turn tool-use loop |
| `backend/vector_store.py` | ChromaDB wrapper; two collections: `course_catalog` (metadata) and `course_content` (chunks) |
| `backend/search_tools.py` | `CourseSearchTool` (tool definition + execution), `ToolManager` (registry) |
| `backend/document_processor.py` | Parses `.txt` course files into `Course`/`Lesson`/`CourseChunk` models; sentence-based chunking |
| `backend/session_manager.py` | In-memory conversation history (keyed by session ID) |
| `backend/config.py` | All tuneable parameters (`CHUNK_SIZE`, `MAX_RESULTS`, `MAX_HISTORY`, model names, etc.) |
| `backend/models.py` | Pydantic models: `Course`, `Lesson`, `CourseChunk` |

### Course Document Format

Documents in `docs/` must follow this plain-text format for `DocumentProcessor` to parse them correctly:

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 1: <lesson title>
Lesson Link: <url>
<lesson content...>

Lesson 2: <lesson title>
...
```

`course_title` is used as the unique ID in ChromaDB — duplicate titles are skipped on reload.

### Tool Design

Adding a new tool requires:
1. Subclass `Tool` (in `search_tools.py`) and implement `get_tool_definition()` + `execute()`.
2. Register it: `tool_manager.register_tool(your_tool)` in `RAGSystem.__init__`.

The tool definition format follows the Anthropic tool-use API schema.
