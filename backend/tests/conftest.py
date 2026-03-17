import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))  # adds backend/ to path

import pytest
from unittest.mock import MagicMock
from vector_store import SearchResults


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.get_lesson_link.return_value = None
    store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    return store


@pytest.fixture
def sample_results():
    return SearchResults(
        documents=["Lesson content here"],
        metadata=[{"course_title": "Python Basics", "lesson_number": 1}],
        distances=[0.1],
    )
