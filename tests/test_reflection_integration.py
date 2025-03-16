"""
Integration tests for the structured reflection system.

These tests verify the complete flow of the reflection system, including:
1. Template loading and usage
2. Tool execution with reflection
3. State management and updates
4. Task completion handling
"""

import asyncio
import os
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from fluent_mcp.core.error_handling import MCPError
from fluent_mcp.core.reflection import ReflectionLoop, ReflectionState
from fluent_mcp.core.reflection_loader import ReflectionLoader
from fluent_mcp.core.tool_registry import register_external_tool


class MockLLMClient:
    """Mock LLM client for testing the reflection system."""

    def __init__(self, responses: List[Dict[str, Any]]):
        self.responses = responses
        self.current_response = 0

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Any = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Return pre-configured responses for testing."""
        if self.current_response >= len(self.responses):
            raise MCPError("No more mock responses available")

        response = self.responses[self.current_response]
        self.current_response += 1
        return response


@pytest.fixture
def mock_templates(tmp_path):
    """Create mock templates for testing."""
    templates_dir = tmp_path / "templates" / "reflection"
    templates_dir.mkdir(parents=True)
    tools_dir = templates_dir / "tools"
    tools_dir.mkdir()

    # Create base templates
    base_reflection = templates_dir / "base_reflection.md"
    base_reflection.write_text(
        """---
name: base_reflection
description: Test base reflection template
application_mode: base
---
# Reflection Template
Original Task: {{original_task}}
Tool: {{tool_name}}
Results: {{tool_results}}
"""
    )

    tool_use = templates_dir / "tool_use.md"
    tool_use.write_text(
        """---
name: tool_use
description: Test tool use template
application_mode: base
---
# Tool Use Template
Task: {{original_task}}
Budget: {{remaining_budget}}/{{initial_budget}}
"""
    )

    # Create tool templates
    gather_thoughts = tools_dir / "gather_thoughts.md"
    gather_thoughts.write_text(
        """---
name: gather_thoughts
description: Test gather thoughts template
tools: ["gather_thoughts"]
---
# Gather Thoughts Template
Analysis: {{analysis}}
Next Steps: {{next_steps}}
"""
    )

    job_complete = tools_dir / "job_complete.md"
    job_complete.write_text(
        """---
name: job_complete
description: Test job complete template
tools: ["job_complete"]
---
# Job Complete Template
Result: {{result}}
"""
    )

    return templates_dir


@pytest.fixture
def reflection_loop(mock_templates):
    """Create a ReflectionLoop instance with mock templates."""
    loader = ReflectionLoader(templates_dir=str(mock_templates))
    return ReflectionLoop(reflection_loader=loader)


@pytest.mark.asyncio
async def test_complete_reflection_flow(reflection_loop):
    """
    Test a complete reflection flow from start to finish.

    This test verifies:
    1. Template loading and formatting
    2. Tool execution with reflection
    3. State updates via gather_thoughts
    4. Task completion via job_complete
    """
    # Mock LLM responses for a complete flow
    mock_responses = [
        # First iteration: Tool execution
        {
            "tool_calls": [
                {"type": "function", "id": "call_1", "function": {"name": "test_tool", "arguments": '{"arg1": "test"}'}}
            ]
        },
        # First reflection: Gather thoughts
        {
            "tool_calls": [
                {
                    "type": "function",
                    "id": "call_2",
                    "function": {
                        "name": "gather_thoughts",
                        "arguments": {
                            "analysis": "Initial analysis",
                            "next_steps": "Continue processing",
                            "workflow_state": "# Progress\n- Step 1 complete",
                            "is_complete": False,
                        },
                    },
                }
            ]
        },
        # Second iteration: Tool execution
        {
            "tool_calls": [
                {
                    "type": "function",
                    "id": "call_3",
                    "function": {"name": "test_tool", "arguments": '{"arg1": "test2"}'},
                }
            ]
        },
        # Final reflection: Complete task
        {
            "tool_calls": [
                {
                    "type": "function",
                    "id": "call_4",
                    "function": {
                        "name": "job_complete",
                        "arguments": {"result": "# Task Complete\n\nSuccessfully processed all steps."},
                    },
                }
            ]
        },
    ]

    # Create mock LLM client
    llm_client = MockLLMClient(mock_responses)

    # Register a test tool
    @register_external_tool(name="test_tool", use_reflection=True)
    async def test_tool(arg1: str) -> Dict[str, Any]:
        return {"status": "success", "result": f"Processed {arg1}"}

    # Run the reflection loop
    result = await reflection_loop.run_structured_reflection_loop(
        original_task="Test task", tool_name="test_tool", llm_client=llm_client, initial_budget=5, max_iterations=5
    )

    # Verify the result
    assert result["status"] == "complete"
    assert "Task Complete" in result["result"]
    assert "state" in result

    # Verify state variables
    state = result["state"]
    assert state["original_task"] == "Test task"
    assert state["workflow_state"] == "# Progress\n- Step 1 complete"
    assert not state["is_complete"]  # Should be False until job_complete


@pytest.mark.asyncio
async def test_reflection_budget_exhaustion(reflection_loop):
    """Test that reflection stops when budget is exhausted."""
    # Mock responses that never complete
    mock_responses = [
        # Tool execution
        {
            "tool_calls": [
                {"type": "function", "id": "call_1", "function": {"name": "test_tool", "arguments": '{"arg1": "test"}'}}
            ]
        },
        # Reflection that doesn't complete
        {
            "tool_calls": [
                {
                    "type": "function",
                    "id": "call_2",
                    "function": {
                        "name": "gather_thoughts",
                        "arguments": {
                            "analysis": "Analysis",
                            "next_steps": "Continue",
                            "workflow_state": "# Progress\n- Working",
                            "is_complete": False,
                        },
                    },
                }
            ]
        },
    ] * 3  # Repeat to exceed budget

    llm_client = MockLLMClient(mock_responses)

    # Run with small budget
    result = await reflection_loop.run_structured_reflection_loop(
        original_task="Test task", tool_name="test_tool", llm_client=llm_client, initial_budget=2, max_iterations=5
    )

    # Verify budget exhaustion
    assert result["status"] == "budget_exhausted"
    assert "Budget exhausted" in result["result"]


@pytest.mark.asyncio
async def test_reflection_template_variables(reflection_loop):
    """Test that template variables are correctly substituted."""
    mock_responses = [
        # Tool execution
        {
            "tool_calls": [
                {"type": "function", "id": "call_1", "function": {"name": "test_tool", "arguments": '{"arg1": "test"}'}}
            ]
        },
        # Reflection with variable checking
        {
            "tool_calls": [
                {
                    "type": "function",
                    "id": "call_2",
                    "function": {"name": "job_complete", "arguments": {"result": "Task complete"}},
                }
            ]
        },
    ]

    llm_client = MockLLMClient(mock_responses)

    # Run reflection loop
    result = await reflection_loop.run_structured_reflection_loop(
        original_task="Variable test", tool_name="test_tool", llm_client=llm_client, initial_budget=3
    )

    # Verify template variables in state
    state = result["state"]
    assert state["original_task"] == "Variable test"
    assert state["tool_name"] == "test_tool"
    assert state["initial_budget"] == 3
