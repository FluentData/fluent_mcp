"""
Example demonstrating the structured reflection loop in Fluent MCP.

This example shows how to:
1. Register a basic external tool with reflection enabled
2. Set up a mock LLM client for demonstration
3. Use the reflection loop to accumulate knowledge
4. Complete a task using the job_complete tool
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fluent_mcp.core.error_handling import MCPError
from fluent_mcp.core.llm_client import LLMClient
from fluent_mcp.core.tool_registry import register_external_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client for demonstration purposes."""

    def __init__(self):
        self.iteration = 0
        self.max_iterations = 3
        self.accumulated_knowledge = []

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Simulate chat completion with tool calls.

        This mock implementation demonstrates a typical reflection flow:
        1. First call: Execute the calculator tool
        2. Second call: Use gather_thoughts to analyze and accumulate results
        3. Third call: Use job_complete to finish the task
        """
        self.iteration += 1
        logger.info(f"Mock LLM processing iteration {self.iteration}")

        # Extract the last user message
        user_message = next(msg["content"] for msg in reversed(messages) if msg["role"] == "user")

        # First iteration: Call the calculator tool
        if self.iteration == 1:
            return {
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "call_1",
                        "function": {"name": "calculate", "arguments": '{"expression": "2 + 2"}'},
                    }
                ]
            }

        # Second iteration: Gather thoughts about the result
        elif self.iteration == 2:
            return {
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "call_2",
                        "function": {
                            "name": "gather_thoughts",
                            "arguments": {
                                "analysis": "The calculator returned 4, which is correct for 2 + 2",
                                "next_steps": "We have the basic calculation result, now we can complete the task",
                                "workflow_state": """# Calculation Results

## Operation
- Expression: 2 + 2
- Result: 4

## Verification
- Basic arithmetic check: ✓
- Result type: integer
- No rounding needed

## Confidence
High confidence in the result based on:
- Simple arithmetic operation
- Direct calculation
- No potential edge cases""",
                                "is_complete": True,
                            },
                        },
                    }
                ]
            }

        # Third iteration: Complete the task
        else:
            return {
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "call_3",
                        "function": {
                            "name": "job_complete",
                            "arguments": {
                                "result": """# Calculation Task Complete

## Results
- Expression: 2 + 2
- Result: 4
- Verification: Successful

## Process
1. Performed basic addition
2. Verified the result
3. Documented the outcome

## Analysis
The calculation was straightforward and verified:
- Simple integer addition
- No floating point considerations
- Result matches expected output

## Confidence
High confidence in the result due to:
- Basic arithmetic operation
- Direct calculation method
- Clear verification steps
- No potential edge cases

Task completed successfully with high confidence in the result."""
                            },
                        },
                    }
                ]
            }


@register_external_tool(name="calculate", use_reflection=True, reflection_budget=3)
async def calculate(expression: str) -> Dict[str, Any]:
    """
    A simple calculator tool that demonstrates the reflection loop.

    This tool shows how to:
    1. Use the reflection system for a simple task
    2. Accumulate knowledge in the workflow state
    3. Provide structured output for analysis

    Args:
        expression: The mathematical expression to evaluate

    Returns:
        A dictionary containing the calculation result
    """
    try:
        # Safely evaluate the expression
        result = eval(expression, {"__builtins__": {}}, {})
        return {"status": "success", "result": result, "expression": expression}
    except Exception as e:
        raise MCPError(f"Calculator error: {str(e)}")


async def main():
    """
    Demonstrate the structured reflection loop.

    This example shows:
    1. Tool registration with reflection
    2. Mock LLM client setup
    3. Workflow state accumulation
    4. Task completion process
    """
    # Create mock LLM client
    llm_client = MockLLMClient()

    try:
        # Use the calculator tool with reflection
        result = await calculate(
            expression="2 + 2", task="Calculate 2 + 2 and verify the result is correct", llm_client=llm_client
        )

        logger.info("Task completed successfully:")
        logger.info(result)

    except Exception as e:
        logger.error(f"Error in example: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
