"""
Tests for the ReflectionState class in Fluent MCP.

This test file focuses on unit tests for the ReflectionState class
which manages state across iterations in the structured reflection loop.
"""

from unittest.mock import MagicMock, patch

import pytest

# The import will work once the class is implemented
from fluent_mcp.core.reflection import ReflectionState


class TestReflectionState:
    """Tests for the ReflectionState class."""

    def test_initialization(self):
        """Test that ReflectionState initializes correctly."""
        # This test will pass once the class is implemented
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

    def test_state_history_tracking(self):
        """Test tracking state history."""
        state = ReflectionState("Test task")

        # First iteration
        result1 = {
            "status": "in_progress",
            "analysis": "Analysis 1",
            "next_steps": "Next steps 1",
            "workflow_state": "State 1",
        }
        state.update_from_gather_thoughts(result1)

        # Second iteration
        result2 = {
            "status": "in_progress",
            "analysis": "Analysis 2",
            "next_steps": "Next steps 2",
            "workflow_state": "State 2",
        }
        state.update_from_gather_thoughts(result2)

        # Check history
        assert len(state.history) == 2
        assert state.history[0]["analysis"] == "Analysis 1"
        assert state.history[1]["analysis"] == "Analysis 2"

        # Check current state
        assert state.analysis == "Analysis 2"
        assert state.next_steps == "Next steps 2"
        assert state.workflow_state == "State 2"

    def test_edge_cases(self):
        """Test edge cases for ReflectionState."""
        # Test with zero budget
        state = ReflectionState("Test task", 0)
        assert state.remaining_budget == 0
        assert not state.decrease_budget(1)

        # Test with empty workflow state
        state = ReflectionState("Test task")
        result = {
            "status": "in_progress",
            "analysis": "Test analysis",
            "next_steps": "Test next steps",
            "workflow_state": "",
        }
        state.update_from_gather_thoughts(result)
        assert state.workflow_state == ""

        # Test with None values
        state = ReflectionState("Test task")
        result = {"status": "in_progress", "analysis": None, "next_steps": None, "workflow_state": None}
        state.update_from_gather_thoughts(result)
        assert state.analysis == ""  # Should handle None gracefully
        assert state.next_steps == ""
        assert state.workflow_state == ""

        # Test with extra fields
        result = {
            "status": "in_progress",
            "analysis": "Analysis",
            "next_steps": "Next steps",
            "workflow_state": "State",
            "extra_field": "Extra value",
        }
        state.update_from_gather_thoughts(result)
        # Should ignore extra fields
        assert not hasattr(state, "extra_field")
