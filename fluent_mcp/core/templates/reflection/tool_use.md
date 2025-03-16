---
name: tool_use
description: Standard template for tool usage instructions in the structured reflection loop
application_mode: base
---

# Task Execution Guide

## Original Task
{{original_task}}

## Current Understanding
{{analysis}}

## Planned Actions
{{next_steps}}

## Accumulated Information
{{workflow_state}}

## Available Tools
{{tool_descriptions}}

## Budget Information
You have {{remaining_budget}} iterations remaining out of {{initial_budget}}.
Consider this when selecting tools and planning actions.

## Instructions

### Tool Selection
Based on your next steps plan and the available information:
1. Review the available tools and their capabilities
2. Select the most appropriate tool for your current objective
3. Ensure you have all required information for the tool

### Task Completion Check
Before proceeding, ask yourself:
1. Do I have enough information to complete the task?
2. Have I achieved the original objective?
3. Is the result well-structured and complete?

If you have gathered sufficient information and the task is complete:
- Use the job_complete tool to finish the task
- Format the result according to the appropriate template
- Include all relevant findings and references

If more information is needed:
- Select and use the appropriate tool
- Be specific about what information you need
- Consider the remaining budget

### Tool Usage Guidelines
When using a tool:
1. Provide all required arguments
2. Format arguments correctly
3. Be specific in your requests
4. Consider how the results will contribute to the task

Remember: The goal is to complete the task efficiently while maintaining high quality results.
