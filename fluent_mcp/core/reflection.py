"""
Reflection loop for embedded reasoning.

This module provides functionality for implementing a structured reflection loop
in embedded reasoning, allowing the LLM to reflect on its reasoning process and
improve its performance.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from fluent_mcp.core.reflection_loader import ReflectionLoader
from fluent_mcp.core.tool_registry import get_embedded_tool

logger = logging.getLogger("fluent_mcp.reflection")


class ReflectionState:
    """
    Tracks the state of a reflection process.

    This class maintains the state of a structured reflection process, including
    the original task, budget, analysis, next steps, workflow state, and completion status.
    It also provides methods for updating the state and managing the budget.
    """

    def __init__(self, original_task: str, initial_budget: int = 10):
        """
        Initialize a new reflection state.

        Args:
            original_task: The original task or question to reflect on
            initial_budget: The initial budget for the reflection process
        """
        self.original_task: str = original_task
        self.initial_budget: int = initial_budget
        self.remaining_budget: int = initial_budget
        self.analysis: str = ""
        self.next_steps: str = ""
        self.workflow_state: str = ""
        self.is_complete: bool = False
        self.history: List[Dict[str, Any]] = []

    def decrease_budget(self, amount: int = 1) -> bool:
        """
        Decrease the remaining budget by the specified amount.

        Args:
            amount: The amount to decrease the budget by

        Returns:
            True if the budget was successfully decreased, False if the budget is exhausted
        """
        if self.remaining_budget < amount:
            logger.warning(f"Budget exhausted: {self.remaining_budget} < {amount}")
            return False

        self.remaining_budget -= amount
        logger.debug(f"Budget decreased by {amount}, remaining: {self.remaining_budget}")
        return True

    def update_from_gather_thoughts(self, result: Dict[str, Any]) -> None:
        """
        Update the state from the result of a gather_thoughts operation.

        Args:
            result: The result dictionary from gather_thoughts
        """
        # Update state from result
        if "analysis" in result:
            self.analysis = result["analysis"] if result["analysis"] is not None else ""

        if "next_steps" in result:
            self.next_steps = result["next_steps"] if result["next_steps"] is not None else ""

        if "workflow_state" in result:
            self.workflow_state = result["workflow_state"] if result["workflow_state"] is not None else ""

        # Check if the task is complete
        if "status" in result and result["status"] == "complete":
            self.is_complete = True
            logger.info("Reflection process marked as complete")

        # Save current state to history after updating
        self._save_to_history()

        logger.debug(
            f"State updated from gather_thoughts: analysis={len(self.analysis)} chars, "
            f"next_steps={len(self.next_steps)} chars, "
            f"workflow_state={len(self.workflow_state)} chars, "
            f"is_complete={self.is_complete}"
        )

    def _save_to_history(self) -> None:
        """
        Save the current state to the state history.
        """
        current_state = {
            "analysis": self.analysis,
            "next_steps": self.next_steps,
            "workflow_state": self.workflow_state,
            "remaining_budget": self.remaining_budget,
            "is_complete": self.is_complete,
        }
        self.history.append(current_state)
        logger.debug(f"Saved state to history, history size: {len(self.history)}")

    def get_template_variables(self) -> Dict[str, Any]:
        """
        Get a dictionary of variables for template formatting.

        Returns:
            A dictionary of variables for template formatting
        """
        return {
            "original_task": self.original_task,
            "analysis": self.analysis or "No analysis yet.",
            "next_steps": self.next_steps or "No next steps defined yet.",
            "workflow_state": self.workflow_state or "No workflow state yet.",
            "remaining_budget": self.remaining_budget,
            "initial_budget": self.initial_budget,
            "is_complete": self.is_complete,
            "history_length": len(self.history),
        }


class ReflectionLoop:
    """
    Implements a structured reflection loop for embedded reasoning.

    The reflection loop allows the LLM to reflect on its reasoning process
    and improve its performance through structured reflection templates.
    """

    def __init__(self, reflection_loader: Optional[ReflectionLoader] = None):
        """
        Initialize a new reflection loop.

        Args:
            reflection_loader: Optional reflection loader instance
        """
        self.reflection_loader = reflection_loader or ReflectionLoader()

    def _format_template_with_state(self, template: Dict[str, Any], state: ReflectionState) -> str:
        """
        Format a template using the reflection state.

        Args:
            template: The template to format
            state: The reflection state to use for variables

        Returns:
            The formatted template content
        """
        variables = state.get_template_variables()
        return self.reflection_loader.format_reflection_template(template, variables)

    def _format_reflection_template_with_state(
        self,
        template: Dict[str, Any],
        state: ReflectionState,
        tool_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Format a reflection template with state and tool result.

        Args:
            template: The template to format
            state: The reflection state to use for variables
            tool_result: Optional tool result to include in the template

        Returns:
            The formatted template content
        """
        variables = state.get_template_variables()

        # Add tool result variables if available
        if tool_result:
            variables.update(
                {
                    "tool_name": tool_result.get("function_name", ""),
                    "tool_arguments": tool_result.get("arguments", {}),
                    "tool_results": tool_result.get("result", ""),
                }
            )

        return self.reflection_loader.format_reflection_template(template, variables)

    def _check_for_job_complete(self, tool_calls: List[Dict[str, Any]]) -> bool:
        """
        Check if job_complete tool was called.

        Args:
            tool_calls: List of tool calls to check

        Returns:
            True if job_complete was called, False otherwise
        """
        for tool_call in tool_calls:
            if tool_call["type"] == "function":
                name = tool_call["function"]["name"]
                if name == "job_complete" or name.endswith("_job_complete"):
                    return True
        return False

    def _check_for_gather_thoughts(self, tool_calls: List[Dict[str, Any]]) -> bool:
        """
        Check if gather_thoughts tool was called.

        Args:
            tool_calls: List of tool calls to check

        Returns:
            True if gather_thoughts was called, False otherwise
        """
        for tool_call in tool_calls:
            if tool_call["type"] == "function" and tool_call["function"]["name"] == "gather_thoughts":
                return True
        return False

    def _get_gather_thoughts_result(
        self, tool_calls: List[Dict[str, Any]], tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract result from gather_thoughts tool call.

        Args:
            tool_calls: List of tool calls
            tool_results: Optional list of tool results. If not provided, returns the arguments from the tool call.

        Returns:
            A dictionary containing the gather_thoughts result, or an empty dict if no tool call found
        """
        for i, tool_call in enumerate(tool_calls):
            if tool_call["type"] == "function" and tool_call["function"]["name"] == "gather_thoughts":
                if tool_results and i < len(tool_results):
                    return tool_results[i]
                else:
                    # If no tool results provided, return the arguments as the result
                    args = tool_call["function"]["arguments"]
                    is_complete = args.get("is_complete", False)
                    return {
                        "status": "complete" if is_complete else "in_progress",
                        "analysis": args.get("analysis", ""),
                        "next_steps": args.get("next_steps", ""),
                        "workflow_state": args.get("workflow_state", ""),
                        "is_complete": is_complete,
                    }
        return {}

    def _get_job_complete_result(
        self, tool_calls: List[Dict[str, Any]], tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract result from job_complete tool call.

        Args:
            tool_calls: List of tool calls
            tool_results: Optional list of tool results. If not provided, returns the arguments from the tool call.

        Returns:
            A dictionary containing the job_complete result, or an error status if no tool call found
        """
        # If tool_results is a string, it's an error from the test
        if isinstance(tool_results, str):
            tool_results = None

        for i, tool_call in enumerate(tool_calls):
            if tool_call["type"] == "function" and (
                tool_call["function"]["name"] == "job_complete"
                or tool_call["function"]["name"].endswith("_job_complete")
            ):
                if tool_results and i < len(tool_results):
                    return tool_results[i]
                else:
                    # If no tool results provided, return the arguments as the result
                    args = tool_call["function"]["arguments"]
                    return {
                        "status": "complete",
                        "result": args.get("result", ""),
                    }
        return {
            "status": "error",
            "error": "no result found for job_complete tool call",
        }

    async def run_structured_reflection_loop(
        self,
        original_task: str,
        tool_name: str,
        llm_client: Any,
        initial_budget: int = 10,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        Run a structured reflection loop.

        This method implements the main reflection loop that:
        1. Creates a ReflectionState to track progress
        2. Gets tool-specific job_complete function if available
        3. Runs the main reflection loop until completion, budget exhaustion, or max iterations
        4. Handles tool calls and gather_thoughts updates
        5. Returns appropriate result based on completion status

        Args:
            original_task: The original task or question to reflect on
            tool_name: The name of the tool to use for the task
            llm_client: The LLM client to use for reflection
            initial_budget: Initial budget for the reflection process
            max_iterations: Maximum number of reflection iterations

        Returns:
            A dictionary containing the final result and status
        """
        logger.info(f"Starting structured reflection loop for tool: {tool_name}")

        # Create reflection state
        state = ReflectionState(original_task, initial_budget)

        # Get tool-specific job_complete function if available
        tool_specific_job_complete = get_embedded_tool(f"{tool_name}_job_complete")

        # Track iterations
        iteration = 0

        while iteration < max_iterations and not state.is_complete:
            iteration += 1
            logger.info(f"Starting reflection iteration {iteration}")

            # Check budget
            if not state.decrease_budget(1):
                logger.warning("Budget exhausted")
                return {
                    "status": "budget_exhausted",
                    "result": "Budget exhausted before completion",
                    "state": state.get_template_variables(),
                }

            # Get tool template
            tool_template = self.reflection_loader.get_tool_template(tool_name)

            # Format template with state
            formatted_template = self._format_template_with_state(tool_template, state)

            # Run tool with LLM
            tool_result = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are using a tool to complete a task."},
                    {"role": "user", "content": formatted_template},
                ],
                tools=get_embedded_tool(tool_name),
                temperature=0.3,
            )

            # Check for errors
            if tool_result.get("error"):
                logger.error(f"Error in tool execution: {tool_result['error']}")
                return {
                    "status": "error",
                    "result": f"Error in tool execution: {tool_result['error']}",
                    "state": state.get_template_variables(),
                }

            # Get tool calls and results
            tool_calls = tool_result.get("tool_calls", [])
            tool_results = []

            # Execute tool calls
            for tool_call in tool_calls:
                if tool_call["type"] == "function":
                    tool = get_embedded_tool(tool_call["function"]["name"])
                    if tool:
                        result = await tool(**tool_call["function"]["arguments"])
                        tool_results.append(result)

            # Check for job completion
            if self._check_for_job_complete(tool_calls):
                job_result = self._get_job_complete_result(tool_calls, tool_results)
                if job_result:
                    return {
                        "status": "complete",
                        "result": job_result["result"],
                        "state": state.get_template_variables(),
                    }

            # Check for gather_thoughts
            if self._check_for_gather_thoughts(tool_calls):
                gather_result = self._get_gather_thoughts_result(tool_calls, tool_results)
                if gather_result:
                    state.update_from_gather_thoughts(gather_result)

            # Get reflection template
            reflection_template = self.reflection_loader.get_reflection_template()

            # Format reflection template with state and tool result
            formatted_reflection = self._format_reflection_template_with_state(
                reflection_template,
                state,
                tool_results[-1] if tool_results else None,
            )

            # Run reflection with LLM
            reflection_result = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are reflecting on your progress."},
                    {"role": "user", "content": formatted_reflection},
                ],
                tools=[get_embedded_tool("gather_thoughts"), get_embedded_tool("job_complete")],
                temperature=0.3,
            )

            # Check for errors
            if reflection_result.get("error"):
                logger.error(f"Error in reflection: {reflection_result['error']}")
                return {
                    "status": "error",
                    "result": f"Error in reflection: {reflection_result['error']}",
                    "state": state.get_template_variables(),
                }

            # Get reflection tool calls and results
            reflection_tool_calls = reflection_result.get("tool_calls", [])
            reflection_tool_results = []

            # Execute reflection tool calls
            for tool_call in reflection_tool_calls:
                if tool_call["type"] == "function":
                    tool = get_embedded_tool(tool_call["function"]["name"])
                    if tool:
                        result = await tool(**tool_call["function"]["arguments"])
                        reflection_tool_results.append(result)

            # Check for job completion in reflection
            if self._check_for_job_complete(reflection_tool_calls):
                job_result = self._get_job_complete_result(reflection_tool_calls, reflection_tool_results)
                if job_result:
                    return {
                        "status": "complete",
                        "result": job_result["result"],
                        "state": state.get_template_variables(),
                    }

            # Check for gather_thoughts in reflection
            if self._check_for_gather_thoughts(reflection_tool_calls):
                gather_result = self._get_gather_thoughts_result(reflection_tool_calls, reflection_tool_results)
                if gather_result:
                    state.update_from_gather_thoughts(gather_result)

        # Return result based on completion status
        if state.is_complete:
            return {
                "status": "complete",
                "result": "Task completed successfully",
                "state": state.get_template_variables(),
            }
        else:
            return {
                "status": "max_iterations",
                "result": "Maximum iterations reached without completion",
                "state": state.get_template_variables(),
            }

    async def run_reflection(
        self,
        previous_reasoning: str,
        tool_calls: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        llm_client: Any,
        system_prompt: str,
        user_prompt: str,
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Run a reflection loop to improve reasoning.

        Args:
            previous_reasoning: The previous reasoning output from the LLM
            tool_calls: List of tool calls made in the previous reasoning
            tool_results: List of tool results from the previous reasoning
            llm_client: The LLM client to use for reflection
            system_prompt: The original system prompt
            user_prompt: The original user prompt
            max_iterations: Maximum number of reflection iterations

        Returns:
            A dictionary containing the final reasoning output
        """
        logger.info(f"Starting reflection loop with max {max_iterations} iterations")

        # Track iterations
        iteration = 0
        current_reasoning = previous_reasoning
        current_tool_calls = tool_calls
        current_tool_results = tool_results

        # Store reflection history
        reflection_history = []

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Starting reflection iteration {iteration}")

            # Get tool names from tool calls
            tool_names = [
                tool_call["function"]["name"] for tool_call in current_tool_calls if tool_call["type"] == "function"
            ]

            # Get reflection template
            reflection_template = self._get_combined_reflection_template(tool_names)

            # Format reflection template with variables
            formatted_template = self._format_reflection_template(
                reflection_template,
                {
                    "previous_reasoning": current_reasoning,
                    "tool_calls": self._format_tool_calls(current_tool_calls),
                    "tool_results": self._format_tool_results(current_tool_results),
                    "domain_context": "No specific domain context provided.",
                    "domain_expert_approach": "No specific domain expert approach provided.",
                    "revised_approach": "To be determined based on reflection.",
                },
            )

            # Run reflection with LLM
            reflection_result = await self._run_reflection_with_llm(
                llm_client, formatted_template, system_prompt, user_prompt
            )

            # Store reflection in history
            reflection_history.append(
                {
                    "iteration": iteration,
                    "reflection": reflection_result["content"],
                    "tool_calls": reflection_result.get("tool_calls", []),
                }
            )

            # If no tool calls in reflection, we're done
            if not reflection_result.get("tool_calls"):
                logger.info(f"Reflection iteration {iteration} complete with no tool calls")
                break

            # Update current reasoning and tool calls for next iteration
            current_reasoning = reflection_result["content"]
            current_tool_calls = reflection_result.get("tool_calls", [])

            # Execute tool calls if any
            if current_tool_calls:
                current_tool_results = await self._execute_reflection_tool_calls(current_tool_calls)
            else:
                current_tool_results = []

        # Return final result
        return {
            "status": "complete",
            "content": current_reasoning,
            "tool_calls": current_tool_calls,
            "tool_results": current_tool_results,
            "reflection_history": reflection_history,
            "iterations": iteration,
        }

    def _get_combined_reflection_template(self, tool_names: List[str]) -> Dict[str, Any]:
        """
        Get the combined reflection template for the given tool names.

        Args:
            tool_names: List of tool names to get reflection templates for

        Returns:
            A dictionary containing the combined reflection template
        """
        # If no tool names, use base reflection template
        if not tool_names:
            return self.reflection_loader.get_reflection_template()

        # Get reflection template for each tool and combine them
        combined_template = self.reflection_loader.get_reflection_template()

        # For simplicity, just use the first tool's template
        # In a more sophisticated implementation, we could combine templates
        # from multiple tools based on priority or other criteria
        if tool_names:
            tool_template = self.reflection_loader.get_reflection_template(tool_names[0])
            if tool_template:
                combined_template = tool_template

        return combined_template

    def _format_reflection_template(self, template: Dict[str, Any], variables: Dict[str, Any]) -> str:
        """
        Format a reflection template with variables.

        Args:
            template: The reflection template dictionary
            variables: Variables to substitute in the template

        Returns:
            The formatted template content
        """
        return self.reflection_loader.format_reflection_template(template, variables)

    def _format_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> str:
        """
        Format tool calls for inclusion in the reflection template.

        Args:
            tool_calls: List of tool calls to format

        Returns:
            Formatted tool calls as a string
        """
        if not tool_calls:
            return "No tool calls were made."

        formatted_calls = []
        for i, tool_call in enumerate(tool_calls):
            if tool_call["type"] == "function":
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                formatted_calls.append(f"Tool Call {i+1}:\n" f"Function: {function_name}\n" f"Arguments: {arguments}\n")

        return "\n".join(formatted_calls)

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """
        Format tool results for inclusion in the reflection template.

        Args:
            tool_results: List of tool results to format

        Returns:
            Formatted tool results as a string
        """
        if not tool_results:
            return "No tool results available."

        formatted_results = []
        for i, result in enumerate(tool_results):
            function_name = result.get("function_name", "Unknown")
            tool_result = result.get("result", "No result")
            formatted_results.append(f"Tool Result {i+1}:\n" f"Function: {function_name}\n" f"Result: {tool_result}\n")

        return "\n".join(formatted_results)

    async def _run_reflection_with_llm(
        self, llm_client: Any, reflection_template: str, system_prompt: str, user_prompt: str
    ) -> Dict[str, Any]:
        """
        Run reflection with the LLM.

        Args:
            llm_client: The LLM client to use for reflection
            reflection_template: The formatted reflection template
            system_prompt: The original system prompt
            user_prompt: The original user prompt

        Returns:
            The LLM response
        """
        # In a real implementation, this would call the LLM client
        # For now, we'll just return a placeholder
        logger.info("Running reflection with LLM")

        # Create a combined prompt for reflection
        reflection_system_prompt = (
            f"{system_prompt}\n\n"
            "You are now in reflection mode. Review your previous reasoning "
            "and improve your approach based on the reflection template."
        )

        reflection_user_prompt = f"Original request: {user_prompt}\n\n" f"Reflection template:\n{reflection_template}"

        # Call the LLM client
        # This is a placeholder - in a real implementation, we would call the actual LLM client
        # result = await llm_client.generate(reflection_system_prompt, reflection_user_prompt)

        # For now, return a placeholder result
        # In the actual implementation, this would be replaced with the real LLM call
        result = {
            "status": "complete",
            "content": "This is a placeholder for the reflection result.",
            "tool_calls": [],
        }

        return result

    async def _execute_reflection_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute tool calls made during reflection.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results
        """
        # In a real implementation, this would execute the tool calls
        # For now, we'll just return a placeholder
        logger.info(f"Executing {len(tool_calls)} tool calls from reflection")

        # Placeholder for tool results
        tool_results = []

        for tool_call in tool_calls:
            if tool_call["type"] == "function":
                function_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                # Placeholder for tool result
                tool_result = {
                    "tool_call_id": tool_call["id"],
                    "function_name": function_name,
                    "arguments": arguments,
                    "result": f"Placeholder result for {function_name}",
                }

                tool_results.append(tool_result)

        return tool_results
