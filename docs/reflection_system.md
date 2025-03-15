# Reflection System in Fluent MCP

The Reflection System in Fluent MCP provides a structured approach for language models to reflect on their reasoning process and improve their performance through iterative refinement. This document explains how to use the reflection system and how to customize it for your specific needs.

## Overview

The reflection system works by:

1. Running an initial embedded reasoning process
2. Analyzing the reasoning and tool usage
3. Providing structured feedback through templates
4. Running additional reasoning iterations with improved approaches
5. Returning the final, improved result

This process helps language models to:

- Identify and correct errors in their reasoning
- Improve tool selection and usage
- Handle complex tasks more effectively
- Provide more accurate and comprehensive responses

## Directory Structure

The reflection system uses a hierarchical template structure:

```
fluent_mcp/core/templates/reflection/
├── base_reflection.md       # Base reflection template (applies to all tools)
├── custom_reflection.md     # Domain-specific reflection (optional)
├── tool_use.md              # Tool usage guidelines
└── tools/
    ├── database_reflection.md      # Tool-specific reflection for database tools
    ├── file_operations_reflection.md  # Tool-specific reflection for file operations
    └── ...                 # Other tool-specific reflection templates
```

## Template Hierarchy

The reflection system uses a hierarchical approach to combine templates:

1. **Base Reflection Template**: Applied to all reflection processes
2. **Custom Reflection Template**: Domain-specific reflection that can be customized per project
3. **Tool-Specific Reflection Templates**: Applied based on the tools used in the reasoning process

Each template can specify an `application_mode` in its frontmatter:

- `base`: The template serves as the base for reflection (default for base templates)
- `append`: The template content is appended to the previous level's content (default for custom and tool templates)
- `overwrite`: The template content replaces the previous level's content

## Using the Reflection System

To use the reflection system, simply enable it when calling `run_embedded_reasoning`:

```python
from fluent_mcp.core.llm_client import run_embedded_reasoning

result = await run_embedded_reasoning(
    system_prompt="You are a helpful assistant that can use tools.",
    user_prompt="Please help me with this task...",
    tools=my_tools,
    enable_reflection=True,
    max_reflection_iterations=3
)

# Access reflection history
if "reflection_history" in result:
    for i, reflection in enumerate(result["reflection_history"]):
        print(f"Reflection {i+1}: {reflection['reflection']}")
```

## Template Format

Reflection templates use Markdown with YAML frontmatter. Here's an example:

```markdown
---
name: base_reflection
description: Standard base reflection template that applies to all tools
application_mode: base
---

# Base Reflection Template

## Previous Reasoning
```
{{previous_reasoning}}
```

## Tool Usage Analysis
Review your previous reasoning and tool usage:

1. Did you correctly understand the user's request?
2. Did you select the most appropriate tools for the task?
3. ...

## Improvement Plan
Based on your analysis, outline specific improvements for your next attempt:

1. How will you better understand the user's request?
2. Which tools will you use and why?
3. ...
```

## Creating Custom Templates

You can create custom reflection templates for specific domains or tools:

### Domain-Specific Template

```markdown
---
name: custom_reflection
description: Domain-specific reflection for financial analysis
application_mode: append
---

# Financial Analysis Reflection

## Domain-Specific Considerations
When reflecting on financial analysis tasks:

1. Did you consider all relevant financial metrics?
2. Did you apply appropriate financial models?
3. ...
```

### Tool-Specific Template

```markdown
---
name: database_reflection
description: Tool-specific reflection for database operations
application_mode: append
tools:
  - query_database
  - update_database
  - create_table
---

# Database Operations Reflection

## Database-Specific Considerations
When working with database operations, consider:

1. Did you use the most efficient query structure?
2. Did you properly handle database connections?
3. ...
```

## Customizing the Reflection Process

You can customize the reflection process by:

1. **Creating new templates**: Add new templates to the appropriate directories
2. **Modifying existing templates**: Update the content of existing templates
3. **Changing application modes**: Adjust how templates are combined
4. **Extending the ReflectionLoop class**: Implement custom reflection logic

## Advanced Usage

For advanced usage, you can directly use the `ReflectionLoop` class:

```python
from fluent_mcp.core.reflection import ReflectionLoop
from fluent_mcp.core.reflection_loader import ReflectionLoader

# Create a custom reflection loader
reflection_loader = ReflectionLoader(templates_dir="/path/to/custom/templates")

# Create a reflection loop instance
reflection_loop = ReflectionLoop(reflection_loader=reflection_loader)

# Run the reflection process
reflection_result = await reflection_loop.run_reflection(
    previous_reasoning="Initial reasoning output...",
    tool_calls=initial_tool_calls,
    tool_results=initial_tool_results,
    llm_client=my_llm_client,
    system_prompt="System prompt...",
    user_prompt="User prompt...",
    max_iterations=5
)
```

## Best Practices

1. **Start with base templates**: Use the provided base templates as a starting point
2. **Create domain-specific templates**: Add domain knowledge to improve reflection
3. **Create tool-specific templates**: Add specialized guidance for complex tools
4. **Use clear placeholders**: Make sure templates have clear placeholders for dynamic content
5. **Balance detail and brevity**: Provide enough guidance without overwhelming the model
6. **Test and iterate**: Refine templates based on actual performance

## Conclusion

The reflection system in Fluent MCP provides a powerful way to improve the reasoning capabilities of language models. By using structured templates and iterative refinement, you can help models better understand tasks, select appropriate tools, and provide more accurate and comprehensive responses. 