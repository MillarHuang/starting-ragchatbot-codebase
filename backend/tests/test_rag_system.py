import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def rag_system():
    with patch("rag_system.VectorStore"), \
         patch("rag_system.AIGenerator"), \
         patch("rag_system.SessionManager"), \
         patch("rag_system.DocumentProcessor"):

        from rag_system import RAGSystem

        config = MagicMock()
        config.ANTHROPIC_API_KEY = "test-key"
        config.ANTHROPIC_MODEL = "test-model"
        config.CHROMA_PATH = "/tmp/test"
        config.EMBEDDING_MODEL = "test-embedding"
        config.MAX_RESULTS = 5
        config.CHUNK_SIZE = 200
        config.CHUNK_OVERLAP = 20
        config.MAX_HISTORY = 10

        system = RAGSystem(config)

        # Replace with controlled mocks
        system.ai_generator = MagicMock()
        system.session_manager = MagicMock()
        system.tool_manager = MagicMock()

        system.ai_generator.generate_response.return_value = "Answer"
        system.tool_manager.get_last_sources.return_value = ["Source"]
        system.session_manager.get_conversation_history.return_value = "history"

        return system


def test_query_returns_tuple_of_response_and_sources(rag_system):
    result = rag_system.query("What is Python?")
    assert result == ("Answer", ["Source"])


def test_query_wraps_input_in_prompt_format(rag_system):
    rag_system.query("What is Python?")
    call_kwargs = rag_system.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["query"] == "Answer this question about course materials: What is Python?"


def test_query_without_session_id_skips_history(rag_system):
    rag_system.query("What is Python?")
    rag_system.session_manager.get_conversation_history.assert_not_called()
    call_kwargs = rag_system.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["conversation_history"] is None


def test_query_with_session_id_passes_history(rag_system):
    rag_system.session_manager.get_conversation_history.return_value = "previous history"
    rag_system.query("What is Python?", session_id="session123")
    call_kwargs = rag_system.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["conversation_history"] == "previous history"


def test_query_updates_session_with_raw_query(rag_system):
    rag_system.query("What is Python?", session_id="session123")
    rag_system.session_manager.add_exchange.assert_called_once_with(
        "session123", "What is Python?", "Answer"
    )


def test_query_sources_reset_after_retrieval(rag_system):
    rag_system.query("What is Python?")
    rag_system.tool_manager.reset_sources.assert_called_once()


def test_query_returns_sources_from_tool_manager(rag_system):
    rag_system.tool_manager.get_last_sources.return_value = [
        '<a href="http://example.com">Source</a>'
    ]
    _, sources = rag_system.query("What is Python?")
    assert '<a href="http://example.com">Source</a>' in sources
