---
name: base_reflection
description: Standard base reflection template for the structured reflection loop
application_mode: base
---

# Reflection on Tool Usage

## Original Task
{{original_task}}

## Previous Tool Execution
Tool: {{tool_name}}
Arguments: {{tool_arguments}}
Results: {{tool_results}}

## Current State Analysis

### Progress Made
{{analysis}}

### Next Steps
{{next_steps}}

### Accumulated Knowledge
{{workflow_state}}

## Reflection Questions
1. What new information did you learn from this tool execution?
2. How does this information relate to what you already know?
3. What important facts should be added to your workflow state?
4. What is your next step, and why?
5. Is the task complete, or do you need more information?

## Budget Status
You have {{remaining_budget}} iterations remaining out of {{initial_budget}}.

## Instructions
Use the gather_thoughts tool to:
1. Provide your analysis of the current situation
2. Plan your next steps
3. Update the workflow_state with accumulated information
4. Indicate if the task is complete

Remember to:
- Structure the workflow_state using markdown formatting
- Be specific about what you learned and what you still need to know
- Consider the remaining budget when planning next steps
- Only mark the task as complete when you have sufficient information
