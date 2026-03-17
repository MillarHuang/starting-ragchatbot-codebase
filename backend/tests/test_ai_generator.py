import pytest
from unittest.mock import MagicMock, patch
from anthropic.types import TextBlock, ToolUseBlock


def make_response(stop_reason, content):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = content
    return resp


@pytest.fixture
def mock_client():
    with patch("ai_generator.anthropic.Anthropic") as MockAnthropic:
        client = MagicMock()
        MockAnthropic.return_value = client
        yield client


@pytest.fixture
def generator(mock_client):
    from ai_generator import AIGenerator
    return AIGenerator(api_key="test-key", model="claude-test")


def test_direct_response_when_no_tool_use(mock_client, generator):
    mock_client.messages.create.return_value = make_response(
        "end_turn", [TextBlock(type="text", text="Hello world")]
    )
    result = generator.generate_response(query="test")
    assert result == "Hello world"


def test_tool_execution_triggered_when_stop_reason_is_tool_use(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="abc", name="search_course_content", input={"query": "python"}
    )
    first_response = make_response("tool_use", [tool_block])
    second_response = make_response("end_turn", [TextBlock(type="text", text="Final answer")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "search results"

    generator.generate_response(query="test", tool_manager=tool_manager)
    assert tool_manager.execute_tool.called


def test_tool_name_and_inputs_passed_to_tool_manager(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="abc", name="search_course_content", input={"query": "python"}
    )
    first_response = make_response("tool_use", [tool_block])
    second_response = make_response("end_turn", [TextBlock(type="text", text="Final answer")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "search results"

    generator.generate_response(query="test", tool_manager=tool_manager)
    tool_manager.execute_tool.assert_called_once_with("search_course_content", query="python")


def test_tool_result_included_in_second_api_call(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="tool_id_1", name="search_course_content", input={"query": "python"}
    )
    first_response = make_response("tool_use", [tool_block])
    second_response = make_response("end_turn", [TextBlock(type="text", text="Final answer")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "search results"

    generator.generate_response(query="test", tool_manager=tool_manager)

    second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
    messages = second_call_kwargs["messages"]
    tool_result_found = any(
        isinstance(msg.get("content"), list)
        and any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in msg.get("content", [])
        )
        for msg in messages
    )
    assert tool_result_found


def test_second_api_call_made_with_tools(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="abc", name="search_course_content", input={"query": "python"}
    )
    first_response = make_response("tool_use", [tool_block])
    second_response = make_response("end_turn", [TextBlock(type="text", text="Final answer")])
    mock_client.messages.create.side_effect = [first_response, second_response]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response(
        query="test", tool_manager=tool_manager, tools=[{"name": "test_tool"}]
    )

    second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
    assert "tools" in second_call_kwargs


def test_tool_use_without_tool_manager_returns_empty_string(mock_client, generator):
    # Bug 1 was: content[0].text raised AttributeError when block is ToolUseBlock.
    # Fix: iterate blocks looking for TextBlock; return "" if none found.
    tool_block = ToolUseBlock(
        type="tool_use", id="abc", name="search_course_content", input={"query": "python"}
    )
    mock_client.messages.create.return_value = make_response("tool_use", [tool_block])
    result = generator.generate_response(query="test", tool_manager=None)
    assert isinstance(result, str)


def test_conversation_history_included_in_system_prompt(mock_client, generator):
    mock_client.messages.create.return_value = make_response(
        "end_turn", [TextBlock(type="text", text="answer")]
    )
    generator.generate_response(query="test", conversation_history="User: hi\nAI: hello")
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "User: hi" in call_kwargs["system"]


def test_no_history_uses_base_system_prompt(mock_client, generator):
    mock_client.messages.create.return_value = make_response(
        "end_turn", [TextBlock(type="text", text="answer")]
    )
    generator.generate_response(query="test")
    call_kwargs = mock_client.messages.create.call_args.kwargs
    from ai_generator import AIGenerator
    assert call_kwargs["system"] == AIGenerator.SYSTEM_PROMPT


def test_max_tool_rounds_constant_equals_2():
    from ai_generator import AIGenerator
    assert AIGenerator.MAX_TOOL_ROUNDS == 2


def test_two_sequential_tool_calls_both_executed(mock_client, generator):
    tool_block1 = ToolUseBlock(
        type="tool_use", id="id1", name="search_course_content", input={"query": "python"}
    )
    tool_block2 = ToolUseBlock(
        type="tool_use", id="id2", name="search_course_content", input={"query": "django"}
    )
    r1 = make_response("tool_use", [tool_block1])
    r2 = make_response("tool_use", [tool_block2])
    r3 = make_response("end_turn", [TextBlock(type="text", text="Final synthesis")])
    mock_client.messages.create.side_effect = [r1, r2, r3]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    result = generator.generate_response(query="test", tool_manager=tool_manager)

    assert tool_manager.execute_tool.call_count == 2
    assert result == "Final synthesis"


def test_loop_stops_after_max_rounds(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="id1", name="search_course_content", input={"query": "q"}
    )
    # 4 tool_use responses, but loop should stop after MAX_TOOL_ROUNDS
    responses = [make_response("tool_use", [tool_block]) for _ in range(4)]
    responses.append(make_response("end_turn", [TextBlock(type="text", text="done")]))
    mock_client.messages.create.side_effect = responses

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response(query="test", tool_manager=tool_manager)

    # 1 initial call + 2 loop rounds = 3 total
    assert mock_client.messages.create.call_count == 3


def test_tool_execution_error_causes_early_exit(mock_client, generator):
    tool_block = ToolUseBlock(
        type="tool_use", id="id1", name="search_course_content", input={"query": "q"}
    )
    r1 = make_response("tool_use", [tool_block])
    r2 = make_response("end_turn", [TextBlock(type="text", text="recovered")])
    mock_client.messages.create.side_effect = [r1, r2]

    tool_manager = MagicMock()
    tool_manager.execute_tool.side_effect = Exception("search failed")

    result = generator.generate_response(query="test", tool_manager=tool_manager)

    # Initial call + 1 follow-up after error result appended = 2
    assert mock_client.messages.create.call_count == 2
    assert isinstance(result, str)


def test_messages_accumulate_across_two_rounds(mock_client, generator):
    tool_block1 = ToolUseBlock(
        type="tool_use", id="id1", name="search_course_content", input={"query": "a"}
    )
    tool_block2 = ToolUseBlock(
        type="tool_use", id="id2", name="search_course_content", input={"query": "b"}
    )
    r1 = make_response("tool_use", [tool_block1])
    r2 = make_response("tool_use", [tool_block2])
    r3 = make_response("end_turn", [TextBlock(type="text", text="done")])
    mock_client.messages.create.side_effect = [r1, r2, r3]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response(query="test", tool_manager=tool_manager)

    third_call_kwargs = mock_client.messages.create.call_args_list[2].kwargs
    messages = third_call_kwargs["messages"]
    # user(query), assistant(round1), user(result1), assistant(round2), user(result2)
    assert len(messages) == 5
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert messages[4]["role"] == "user"


def test_tools_present_in_all_round_calls(mock_client, generator):
    tool_block1 = ToolUseBlock(
        type="tool_use", id="id1", name="search_course_content", input={"query": "a"}
    )
    tool_block2 = ToolUseBlock(
        type="tool_use", id="id2", name="search_course_content", input={"query": "b"}
    )
    r1 = make_response("tool_use", [tool_block1])
    r2 = make_response("tool_use", [tool_block2])
    r3 = make_response("end_turn", [TextBlock(type="text", text="done")])
    mock_client.messages.create.side_effect = [r1, r2, r3]

    tool_manager = MagicMock()
    tool_manager.execute_tool.return_value = "results"

    generator.generate_response(
        query="test", tool_manager=tool_manager, tools=[{"name": "search_course_content"}]
    )

    for call in mock_client.messages.create.call_args_list:
        assert "tools" in call.kwargs
