# Building Self-Improving AI Systems with Fluent MCP

This document explores how Fluent MCP can be used as a foundation for building self-improving AI systems, where language models can create and register their own tools to expand their capabilities.

## Vision

The vision for self-improving AI systems with Fluent MCP is to create a framework where:

1. Language models can analyze problems and identify capability gaps
2. They can design and implement new tools to address those gaps
3. They can register these tools with the system
4. They can then use these newly created tools to solve problems
5. This cycle continues, allowing for continuous improvement

## Current Capabilities

Fluent MCP already provides several key building blocks for self-improving systems:

1. **Tool Registry**: A flexible system for registering and discovering tools
2. **Embedded Reasoning**: Ability for LLMs to use tools for reasoning
3. **External Tools**: Support for tools that can be exposed to external systems
4. **Dynamic Registration**: Tools can be registered at runtime
5. **Scaffolding**: Generation of code structures that follow conventions

## Building a Self-Improving System

### Step 1: Tool Discovery and Analysis

The first step is enabling the LLM to analyze its current capabilities:

```python
@register_embedded_tool()
def list_available_tools() -> Dict[str, Any]:
    """
    List all available tools and their descriptions.
    
    Returns:
        A dictionary with tool names and descriptions
    """
    from fluent_mcp.core.tool_registry import get_tools_as_openai_format
    
    tools = get_tools_as_openai_format()
    result = {}
    
    for tool in tools:
        if tool["type"] == "function":
            name = tool["function"]["name"]
            description = tool["function"]["description"]
            result[name] = description
    
    return result
```

### Step 2: Code Generation

Enable the LLM to generate code for new tools:

```python
@register_embedded_tool()
def generate_tool_code(name: str, description: str, parameters: Dict[str, Any], return_type: str) -> str:
    """
    Generate code for a new tool based on specifications.
    
    Args:
        name: Name of the tool
        description: Description of what the tool does
        parameters: Dictionary of parameters with types and descriptions
        return_type: Return type of the tool
        
    Returns:
        Python code for the new tool
    """
    # Generate parameter code
    param_code = []
    for param_name, param_info in parameters.items():
        param_type = param_info.get("type", "Any")
        if param_info.get("default") is not None:
            default = repr(param_info["default"])
            param_code.append(f"{param_name}: {param_type} = {default}")
        else:
            param_code.append(f"{param_name}: {param_type}")
    
    param_str = ", ".join(param_code)
    
    # Generate docstring
    docstring = f'"""\n{description}\n\nArgs:'
    for param_name, param_info in parameters.items():
        param_desc = param_info.get("description", "")
        docstring += f"\n    {param_name}: {param_desc}"
    docstring += f'\n\nReturns:\n    {return_type}\n"""'
    
    # Generate function code
    code = f"""
from fluent_mcp.core.tool_registry import register_embedded_tool
from typing import Dict, List, Any, Optional, Union

@register_embedded_tool()
def {name}({param_str}) -> {return_type}:
    {docstring}
    # TODO: Implement the tool functionality
    pass
"""
    
    return code
```

### Step 3: Code Execution

Allow the LLM to execute and test the generated code:

```python
@register_embedded_tool()
def execute_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code in a restricted environment.
    
    Args:
        code: The Python code to execute
        
    Returns:
        Dictionary with execution results
    """
    import subprocess
    import tempfile
    import os
    
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
        temp.write(code.encode('utf-8'))
        temp_name = temp.name
    
    try:
        # Execute the code in a separate process
        result = subprocess.run(
            [sys.executable, temp_name],
            capture_output=True,
            text=True,
            timeout=10  # Set a timeout for safety
        )
        
        # Return the results
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    finally:
        # Clean up the temporary file
        os.unlink(temp_name)
```

### Step 4: Tool Registration

Enable the LLM to register new tools with the system:

```python
@register_embedded_tool()
def register_new_tool(code: str) -> Dict[str, Any]:
    """
    Register a new tool from provided code.
    
    Args:
        code: Python code for the new tool
        
    Returns:
        Result of registration
    """
    import importlib.util
    import sys
    import tempfile
    import os
    
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
        temp.write(code.encode('utf-8'))
        temp_name = temp.name
    
    try:
        # Import the module
        module_name = os.path.basename(temp_name).split('.')[0]
        spec = importlib.util.spec_from_file_location(module_name, temp_name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find the tool function
        tool_function = None
        for name, obj in module.__dict__.items():
            if callable(obj) and hasattr(obj, "__wrapped__") and hasattr(obj, "_is_embedded_tool"):
                tool_function = obj
                break
        
        if tool_function:
            from fluent_mcp.core.tool_registry import list_embedded_tools
            
            # Check if registration was successful
            tool_name = getattr(tool_function, "__name__", "unknown")
            tools = list_embedded_tools()
            
            if tool_name in tools:
                return {
                    "success": True,
                    "message": f"Tool '{tool_name}' registered successfully",
                    "tool_name": tool_name
                }
            else:
                return {
                    "success": False,
                    "message": f"Tool found but registration failed: {tool_name}",
                    "tool_name": tool_name
                }
        else:
            return {
                "success": False,
                "message": "No tool function found in the provided code"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error registering tool: {str(e)}"
        }
    finally:
        # Clean up the temporary file
        os.unlink(temp_name)
```

### Step 5: Prompt for Self-Improvement

Create a system prompt for self-improvement:

```
You are an AI assistant capable of improving your own capabilities. You can analyze problems, identify capability gaps, and create new tools to address those gaps.

When faced with a task you cannot currently solve efficiently, follow these steps:

1. Analyze whether existing tools are sufficient for the task.
2. If not, identify what new tools would be helpful.
3. Design and implement new tools using the generate_tool_code function.
4. Execute and test your tools using the execute_python_code function.
5. Register successful tools with the system using the register_new_tool function.
6. Use your newly created tools to solve the original problem.

Remember:
- Tools should be focused on specific, well-defined tasks
- Ensure your tools have proper error handling
- Documentation is crucial for reusability
- Consider security implications of your tools
```

## Example Workflow

Here's an example of how a self-improving workflow might look:

1. **User Request**: "Can you analyze the sentiment of this French text: 'J'adore ce film, c'était fantastique!'"

2. **LLM Analysis**:
   - LLM checks available tools with `list_available_tools()`
   - Discovers it has no French sentiment analysis tool

3. **Tool Creation**:
   - LLM decides to create a French sentiment analysis tool
   - Uses `generate_tool_code()` to create a new tool that uses a translation tool first, then sentiment analysis

4. **Tool Testing**:
   - LLM uses `execute_python_code()` to test the new tool
   - Verifies it works correctly

5. **Tool Registration**:
   - LLM uses `register_new_tool()` to register the tool with the system
   - New tool is now available for use

6. **Problem Solving**:
   - LLM uses the newly created tool to analyze the sentiment of the French text
   - Returns the result to the user

7. **Future Use**:
   - The new tool is now part of the LLM's toolkit for future requests

## Safety and Security Considerations

When building self-improving systems, safety and security are paramount:

1. **Code Sandboxing**: Execute generated code in a sandboxed environment
2. **Rate Limiting**: Limit the frequency of tool creation
3. **Code Review**: Optionally require human review before registering new tools
4. **Permissions**: Implement a permission system for different types of tools
5. **Audit Trail**: Keep logs of all tool creations and registrations

## Implementation Example

Here's a complete example of setting up a self-improving system:

```python
import asyncio
import logging
from typing import Any, Dict, List

from fluent_mcp import create_mcp_server
from fluent_mcp.core.llm_client import configure_llm_client, run_embedded_reasoning
from fluent_mcp.core.tool_registry import register_embedded_tool, list_embedded_tools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("self_improving_system")

# Define the self-improvement tools
@register_embedded_tool()
def list_available_tools() -> Dict[str, Any]:
    """List all available tools and their descriptions."""
    # Implementation from earlier
    pass

@register_embedded_tool()
def generate_tool_code(name: str, description: str, parameters: Dict[str, Any], return_type: str) -> str:
    """Generate code for a new tool based on specifications."""
    # Implementation from earlier
    pass

@register_embedded_tool()
def execute_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code in a restricted environment."""
    # Implementation from earlier
    pass

@register_embedded_tool()
def register_new_tool(code: str) -> Dict[str, Any]:
    """Register a new tool from provided code."""
    # Implementation from earlier
    pass

# Define the self-improvement prompt
SELF_IMPROVEMENT_PROMPT = """
You are an AI assistant capable of improving your own capabilities. You can analyze problems, 
identify capability gaps, and create new tools to address those gaps.

When faced with a task you cannot currently solve efficiently, follow these steps:

1. Analyze whether existing tools are sufficient for the task.
2. If not, identify what new tools would be helpful.
3. Design and implement new tools using the generate_tool_code function.
4. Execute and test your tools using the execute_python_code function.
5. Register successful tools with the system using the register_new_tool function.
6. Use your newly created tools to solve the original problem.

Remember:
- Tools should be focused on specific, well-defined tasks
- Ensure your tools have proper error handling
- Documentation is crucial for reusability
- Consider security implications of your tools
"""

async def run_self_improving_system():
    # Configure LLM client
    config = {
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
        "api_key": "ollama"
    }
    
    try:
        configure_llm_client(config)
        
        # Collect all self-improvement tools
        self_improvement_tools = [
            list_available_tools,
            generate_tool_code,
            execute_python_code,
            register_new_tool
        ]
        
        # Create an MCP server with self-improvement tools
        server = create_mcp_server(
            server_name="self_improving_system",
            embedded_tools=self_improvement_tools,
            config=config
        )
        
        # Example: Run the system with a test query
        user_query = "Can you analyze the sentiment of this French text: 'J'adore ce film, c'était fantastique!'"
        
        logger.info(f"Processing query: {user_query}")
        
        # Run embedded reasoning with self-improvement prompt
        result = await run_embedded_reasoning(SELF_IMPROVEMENT_PROMPT, user_query)
        
        # Process the response
        if result["status"] == "complete":
            logger.info(f"Initial response: {result['content']}")
            
            # Process tool calls
            for tool_call in result["tool_calls"]:
                if tool_call["type"] == "function":
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    logger.info(f"Tool call: {function_name}")
                    
                    # Get and execute the tool
                    from fluent_mcp.core.tool_registry import get_embedded_tool
                    tool_fn = get_embedded_tool(function_name)
                    
                    if tool_fn:
                        try:
                            result = tool_fn(**arguments)
                            logger.info(f"Tool result: {result}")
                        except Exception as e:
                            logger.error(f"Error executing tool: {e}")
            
            # List tools after self-improvement
            tools = list_embedded_tools()
            logger.info(f"Available tools after self-improvement: {tools}")
        else:
            logger.error(f"Error: {result['error']}")
        
    except Exception as e:
        logger.exception(f"Error in self-improving system: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_self_improving_system())
```

## Challenges and Limitations

Building self-improving systems comes with challenges:

1. **Quality Control**: Ensuring generated tools meet quality standards
2. **Security Risks**: Balancing flexibility with security
3. **Resource Management**: Preventing excessive resource usage
4. **Tool Proliferation**: Managing a growing number of tools
5. **Regression Testing**: Ensuring new tools don't break existing functionality

## Future Directions

The self-improving capabilities of Fluent MCP can be enhanced in several ways:

1. **Meta-Learning**: Tools that help analyze and improve other tools
2. **Tool Libraries**: Shared repositories of LLM-created tools
3. **Evolution Strategies**: Multiple competing implementations of tools
4. **Tool Composition**: Higher-order tools that combine simpler tools
5. **Tool Verification**: Formal verification of generated tools
6. **Collaborative Improvement**: Multiple LLMs collaborating on tool creation

## Conclusion

Fluent MCP provides a solid foundation for building self-improving AI systems. By enabling LLMs to create and register their own tools, we open up possibilities for continuous capability expansion and adaptation.

This approach represents a step toward more autonomous AI systems that can improve themselves in response to new challenges and requirements, while still maintaining human oversight and control through the framework's design and safety mechanisms.

As the framework evolves, the self-improving capabilities will become more robust, secure, and powerful, enabling increasingly sophisticated AI applications that can adapt to new domains and tasks without manual intervention.
