"""
Tests for the reflection system in Fluent MCP.

This test file focuses on unit tests for the reflection system components,
including ReflectionState, template formatting, and standard tools.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from fluent_mcp.core.reflection import ReflectionLoop, ReflectionState
from fluent_mcp.core.reflection_loader import ReflectionLoader


class TestReflectionState:
    """Tests for the ReflectionState class."""

    def test_initialization(self):
        """Test that ReflectionState initializes correctly."""
        state = ReflectionState("Test task", 10)
        assert state.original_task == "Test task"
        assert state.initial_budget == 10
        assert state.remaining_budget == 10
        assert state.workflow_state == ""
        assert not state.is_complete

    def test_budget_management(self):
        """Test budget decrease and exhaustion detection."""
        state = ReflectionState("Test task", 3)
        assert state.decrease_budget(1)  # 2 remaining
        assert state.remaining_budget == 2
        assert state.decrease_budget(1)  # 1 remaining
        assert state.remaining_budget == 1
        assert state.decrease_budget(1)  # 0 remaining
        assert state.remaining_budget == 0
        assert not state.decrease_budget(1)  # Budget exhausted

    def test_update_from_gather_thoughts(self):
        """Test updating state from gather_thoughts result."""
        state = ReflectionState("Test task")
        result = {
            "status": "in_progress",
            "analysis": "Test analysis",
            "next_steps": "Test next steps",
            "workflow_state": "# Collected Information\n- Item 1\n- Item 2",
        }
        state.update_from_gather_thoughts(result)
        assert state.analysis == "Test analysis"
        assert state.next_steps == "Test next steps"
        assert "Collected Information" in state.workflow_state
        assert not state.is_complete

        # Test completion
        result["status"] = "complete"
        state.update_from_gather_thoughts(result)
        assert state.is_complete

    def test_get_template_variables(self):
        """Test getting template variables from state."""
        state = ReflectionState("Test task")
        state.analysis = "Analysis"
        state.next_steps = "Next steps"
        state.workflow_state = "Workflow state"
        state.remaining_budget = 5

        variables = state.get_template_variables()
        assert variables["original_task"] == "Test task"
        assert variables["analysis"] == "Analysis"
        assert variables["next_steps"] == "Next steps"
        assert variables["workflow_state"] == "Workflow state"
        assert variables["remaining_budget"] == 5


class TestReflectionTemplateFormatting:
    """Tests for reflection template formatting."""

    def test_format_template_with_state(self):
        """Test formatting a template with reflection state."""
        # Create a mock ReflectionLoader
        loader = MagicMock()
        loader.format_reflection_template.return_value = "Formatted template"

        # Create a reflection loop with the mock loader
        loop = ReflectionLoop(reflection_loader=loader)

        # Create a state
        state = ReflectionState("Test task")
        state.analysis = "Analysis"

        # Create a mock template
        template = {"content": "Template content", "config": {}}

        # Format the template
        result = loop._format_template_with_state(template, state)

        # Check that the loader was called correctly
        loader.format_reflection_template.assert_called_once()
        assert result == "Formatted template"

    def test_format_reflection_template_with_state_and_tool_result(self):
        """Test formatting a reflection template with state and tool result."""
        # Create a mock ReflectionLoader
        loader = MagicMock()
        loader.format_reflection_template.return_value = "Formatted reflection"

        # Create a reflection loop with the mock loader
        loop = ReflectionLoop(reflection_loader=loader)

        # Create a state
        state = ReflectionState("Test task")

        # Create a mock tool result
        tool_result = {"function_name": "test_tool", "arguments": {"arg1": "value1"}, "result": "Tool result"}

        # Create a mock template
        template = {"content": "Template content", "config": {}}

        # Format the template
        result = loop._format_reflection_template_with_state(template, state, tool_result)

        # Check that the loader was called correctly
        loader.format_reflection_template.assert_called_once()

        # Get the variables that were passed to the loader
        call_args = loader.format_reflection_template.call_args[0]
        variables = call_args[1]

        # Check that tool result variables were included
        assert variables["tool_name"] == "test_tool"
        assert "arg1" in variables["tool_arguments"]
        assert "Tool result" in variables["tool_results"]
        assert result == "Formatted reflection"


class TestStandardTools:
    """Tests for standard tools in the reflection system."""

    def test_gather_thoughts_tool(self):
        """Test the gather_thoughts tool."""
        from fluent_mcp.core.tool_registry import get_embedded_tool

        # Get the gather_thoughts tool
        gather_thoughts = get_embedded_tool("gather_thoughts")
        assert gather_thoughts is not None

        # Call the tool
        result = gather_thoughts(
            analysis="Test analysis",
            next_steps="Test next steps",
            workflow_state="Test workflow state",
            is_complete=False,
        )

        # Check the result
        assert result["status"] == "in_progress"
        assert result["analysis"] == "Test analysis"
        assert result["next_steps"] == "Test next steps"
        assert result["workflow_state"] == "Test workflow state"

        # Test with is_complete=True
        result = gather_thoughts(
            analysis="Test analysis",
            next_steps="Test next steps",
            workflow_state="Test workflow state",
            is_complete=True,
        )
        assert result["status"] == "complete"

    def test_job_complete_tool(self):
        """Test the job_complete tool."""
        from fluent_mcp.core.tool_registry import get_embedded_tool

        # Get the job_complete tool
        job_complete = get_embedded_tool("job_complete")
        assert job_complete is not None

        # Call the tool
        result = job_complete(result="Test result")

        # Check the result
        assert result["status"] == "complete"
        assert result["result"] == "Test result"

    def test_tool_specific_job_complete_tool(self):
        """Test a tool-specific job_complete tool."""
        from fluent_mcp.core.tool_registry import get_embedded_tool

        # Get the web_research_job_complete tool
        web_research_job_complete = get_embedded_tool("web_research_job_complete")

        # Skip if the tool is not registered yet
        if web_research_job_complete is None:
            pytest.skip("web_research_job_complete tool not registered")

        # Call the tool
        result = web_research_job_complete(
            title="Test title", executive_summary="Test summary", body="Test body", references=["Ref1", "Ref2"]
        )

        # Check the result
        assert result["status"] == "complete"
        assert "Test title" in result["result"]
        assert "Test summary" in result["result"]
        assert "Test body" in result["result"]
        assert "Ref1" in result["result"]
        assert "Ref2" in result["result"]


class TestReflectionLoop:
    """Tests for the ReflectionLoop class."""

    def test_check_for_job_complete(self):
        """Test detecting job_complete tool calls."""
        loop = ReflectionLoop()

        # Create tool calls with job_complete
        tool_calls = [
            {"type": "function", "function": {"name": "job_complete", "arguments": {"result": "Test result"}}}
        ]
        assert loop._check_for_job_complete(tool_calls)

        # Create tool calls with tool-specific job_complete
        tool_calls = [
            {
                "type": "function",
                "function": {
                    "name": "web_research_job_complete",
                    "arguments": {
                        "title": "Test title",
                        "executive_summary": "Test summary",
                        "body": "Test body",
                        "references": ["Ref1", "Ref2"],
                    },
                },
            }
        ]
        assert loop._check_for_job_complete(tool_calls)

        # Create tool calls without job_complete
        tool_calls = [{"type": "function", "function": {"name": "other_tool", "arguments": {"arg1": "value1"}}}]
        assert not loop._check_for_job_complete(tool_calls)

    def test_check_for_gather_thoughts(self):
        """Test detecting gather_thoughts tool calls."""
        loop = ReflectionLoop()

        # Create tool calls with gather_thoughts
        tool_calls = [
            {
                "type": "function",
                "function": {
                    "name": "gather_thoughts",
                    "arguments": {
                        "analysis": "Test analysis",
                        "next_steps": "Test next steps",
                        "workflow_state": "Test state",
                        "is_complete": False,
                    },
                },
            }
        ]
        assert loop._check_for_gather_thoughts(tool_calls)

        # Create tool calls without gather_thoughts
        tool_calls = [{"type": "function", "function": {"name": "other_tool", "arguments": {"arg1": "value1"}}}]
        assert not loop._check_for_gather_thoughts(tool_calls)

    def test_get_gather_thoughts_result(self):
        """Test extracting gather_thoughts result."""
        loop = ReflectionLoop()

        # Create tool calls with gather_thoughts
        tool_calls = [
            {
                "type": "function",
                "function": {
                    "name": "gather_thoughts",
                    "arguments": {
                        "analysis": "Test analysis",
                        "next_steps": "Test next steps",
                        "workflow_state": "Test state",
                        "is_complete": False,
                    },
                },
            }
        ]

        # Extract gather_thoughts result
        result = loop._get_gather_thoughts_result(tool_calls)

        # Check the result
        assert result["analysis"] == "Test analysis"
        assert result["next_steps"] == "Test next steps"
        assert result["workflow_state"] == "Test state"
        assert result["is_complete"] is False

        # Test with missing tool call
        result = loop._get_gather_thoughts_result([])
        assert result == {}

    def test_get_job_complete_result(self):
        """Test extracting job_complete result."""
        loop = ReflectionLoop()

        # Create tool calls with job_complete
        tool_calls = [
            {"type": "function", "function": {"name": "job_complete", "arguments": {"result": "Test result"}}}
        ]

        # Extract job_complete result
        result = loop._get_job_complete_result(tool_calls, "job_complete")

        # Check the result
        assert result["status"] == "complete"
        assert result["result"] == "Test result"

        # Test with missing tool call
        result = loop._get_job_complete_result([], "job_complete")
        assert result["status"] == "error"
        assert "no result found" in result["error"]
