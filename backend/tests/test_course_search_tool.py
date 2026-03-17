import pytest
from unittest.mock import MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


def test_basic_query_returns_formatted_results(mock_vector_store, sample_results):
    mock_vector_store.search.return_value = sample_results
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="what is python")
    assert "[Python Basics - Lesson 1]" in result
    assert "Lesson content here" in result


def test_returns_error_on_search_failure(mock_vector_store):
    mock_vector_store.search.return_value = SearchResults.empty("search failed")
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="python")
    assert result == "search failed"


def test_returns_no_results_message_when_empty(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="python")
    assert result == "No relevant content found."


def test_no_results_includes_course_name_in_message(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="python", course_name="Python Basics")
    assert "in course 'Python Basics'" in result


def test_no_results_includes_lesson_number_in_message(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="python", lesson_number=3)
    assert "in lesson 3" in result


def test_last_sources_populated_after_search(mock_vector_store, sample_results):
    mock_vector_store.search.return_value = sample_results
    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="python")
    assert len(tool.last_sources) == 1


def test_source_with_lesson_link_generates_html_anchor(mock_vector_store, sample_results):
    mock_vector_store.search.return_value = sample_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"
    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="python")
    assert '<a href="' in tool.last_sources[0]


def test_source_without_lesson_link_is_plain_text(mock_vector_store, sample_results):
    mock_vector_store.search.return_value = sample_results
    mock_vector_store.get_lesson_link.return_value = None
    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="python")
    assert tool.last_sources[0] == "Python Basics - Lesson 1"


def test_filters_passed_to_store(mock_vector_store, sample_results):
    mock_vector_store.search.return_value = sample_results
    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="functions", course_name="Python Basics", lesson_number=2)
    mock_vector_store.search.assert_called_once_with(
        query="functions",
        course_name="Python Basics",
        lesson_number=2,
    )
