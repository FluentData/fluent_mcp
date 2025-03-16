# Structured Reflection System

The structured reflection system in Fluent MCP enables tools to reflect on their execution, accumulate knowledge, and make informed decisions about task completion. This document explains how to use and customize the reflection system.

## Overview

### What is Structured Reflection?

The structured reflection loop is a process that allows tools to:
1. Execute actions and analyze their results
2. Accumulate knowledge in a structured workflow state
3. Make decisions about next steps
4. Determine when a task is complete

### Key Components

1. **ReflectionState**: Tracks task progress, budget, and accumulated knowledge
2. **ReflectionLoader**: Manages templates for reflection and tool usage
3. **ReflectionLoop**: Orchestrates the reflection process
4. **Standard Tools**: `gather_thoughts` and `job_complete` for state management

## Template System

### Directory Structure

Templates are located in `fluent_mcp/core/templates/reflection/`:
```
reflection/
├── base_reflection.md    # Base reflection template
├── tool_use.md          # Generic tool usage template
├── custom_reflection.md # Optional custom reflection rules
└── tools/
    ├── gather_thoughts.md  # Template for gather_thoughts tool
    └── job_complete.md     # Template for job_complete tool
```

### Template Types

1. **Base Templates**:
   - `base_reflection.md`: Core reflection structure
   - `tool_use.md`: Standard tool usage guidance

2. **Custom Templates**:
   - `custom_reflection.md`: Project-specific reflection rules
   - Application modes: "append" or "overwrite"

3. **Tool-Specific Templates**:
   - Located in `tools/` directory
   - Can be associated with specific tools
   - Override or extend base templates

### Template Variables

Common variables available in templates:
- `{{original_task}}`: The initial task description
- `{{tool_name}}`: Current tool being used
- `{{tool_arguments}}`: Arguments passed to the tool
- `{{tool_results}}`: Results from tool execution
- `{{analysis}}`: Current analysis of the situation
- `{{next_steps}}`: Planned next actions
- `{{workflow_state}}`: Accumulated knowledge
- `{{remaining_budget}}`: Remaining reflection iterations
- `{{initial_budget}}`: Starting budget

## Using Reflection with Tools

### Registering a Tool with Reflection

Use the `@register_external_tool` decorator with reflection options:

```python
@register_external_tool(
    name="my_tool",
    use_reflection=True,
    reflection_budget=5
)
async def my_tool(arg1: str, arg2: int) -> Dict[str, Any]:
    """Tool implementation"""
    pass
```

Parameters:
- `name`: Optional custom name for the tool
- `use_reflection`: Enable/disable reflection (default: True)
- `reflection_budget`: Maximum reflection iterations (default: 5)

### Required Tool Arguments

When calling a tool with reflection enabled:
```python
result = await my_tool(
    arg1="value1",
    arg2=42,
    task="Description of what to accomplish",  # Required
    llm_client=llm_client  # Required for reflection
)
```

## Workflow State Management

### State Structure

The workflow state should be formatted in markdown:

```markdown
# Task Progress

## Key Findings
- Important discovery 1
- Important discovery 2

## Open Questions
1. Question to investigate
2. Area to explore

## Evidence and Sources
* Source 1: Key points
* Source 2: Relevant information

## Current Status
Summary of where we are in the process
```

### State Updates

Use the `gather_thoughts` tool to update state:
```python
{
    "analysis": "Current situation analysis",
    "next_steps": "Planned actions",
    "workflow_state": "Markdown formatted state",
    "is_complete": False  # or True when done
}
```

## Best Practices

1. **Task Description**:
   - Be specific about objectives
   - Include success criteria
   - Specify any constraints

2. **Workflow State**:
   - Use clear hierarchical structure
   - Keep information organized by topic
   - Update incrementally
   - Link related information

3. **Reflection Budget**:
   - Set based on task complexity
   - Consider cost/performance tradeoffs
   - Monitor usage patterns

4. **Template Customization**:
   - Start with base templates
   - Add tool-specific templates as needed
   - Use custom templates for project standards

## Troubleshooting

### Common Issues

1. **Template Not Found**:
   - Check template directory structure
   - Verify template names match configuration
   - Ensure proper file extensions (.md)

2. **Budget Exhaustion**:
   - Increase reflection_budget if needed
   - Check for infinite loops
   - Optimize decision making

3. **State Management**:
   - Verify markdown formatting
   - Check for missing sections
   - Ensure proper variable substitution

4. **LLM Integration**:
   - Confirm llm_client is provided
   - Check API configuration
   - Verify tool registration

### Debug Tips

1. Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Monitor template loading:
```python
loader = ReflectionLoader()
loader.load_templates()  # Check logs for loading status
```

3. Inspect state updates:
```python
print(state.get_template_variables())  # View current state
```

## Example Implementation

See `fluent_mcp/examples/structured_reflection_example.py` for a complete example showing:
1. Tool registration with reflection
2. Mock LLM client setup
3. Workflow state accumulation
4. Task completion process

## Advanced Topics

1. **Custom Template Creation**:
   - Follow frontmatter format
   - Define application mode
   - Specify tool associations

2. **State Persistence**:
   - Implement custom state storage
   - Handle long-running tasks
   - Manage state across sessions

3. **Integration Patterns**:
   - Combine multiple tools
   - Chain reflection loops
   - Share workflow state

4. **Error Recovery**:
   - Handle partial results
   - Implement retry logic
   - Preserve state on failure 