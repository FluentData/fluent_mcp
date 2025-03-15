# Fluent MCP API Reference

This document provides a comprehensive reference for the Fluent MCP API.

## Core Modules

### fluent_mcp

The main package that provides high-level functions.

#### Functions

- `scaffold_server(output_dir, server_name, description=None, author=None, email=None) -> Dict[str, str]`
  
  Creates a new MCP server project with the necessary file structure.
  
  - `output_dir`: Directory where the server will be created
  - `server_name`: Name of the server
  - `description`: Optional description of the server
  - `author`: Optional author name
  - `email`: Optional author email
  - Returns: Dictionary with the path to the created server

- `create_mcp_server(server_name, embedded_tools=None, external_tools=None, prompts=None, prompts_dir=None, config=None) -> Server`
  
  Creates and configures an MCP server.
  
  - `server_name`: Name of the server
  - `embedded_tools`: List of embedded tools to register
  - `external_tools`: List of external tools to register
  - `prompts`: List of prompts to register
  - `prompts_dir`: Directory containing prompt files
  - `config`: Configuration dictionary
  - Returns: Configured server instance

### fluent_mcp.core.llm_client

Module for interacting with language models.

#### Classes

- `LLMClient`
  
  Client for interacting with language models.
  
  - `__init__(config: Dict[str, Any])`
    - `config`: LLM configuration dictionary
  
  - `async chat_completion(messages, tools=None, temperature=0.3, max_tokens=1000) -> Dict[str, Any]`
    - `messages`: List of conversation messages
    - `tools`: List of tools in OpenAI format
    - `temperature`: Sampling temperature
    - `max_tokens`: Maximum tokens to generate
    - Returns: Dictionary with response and tool calls

- `LLMClientError`
  
  Base exception for LLM client errors.

- `LLMClientConfigError`
  
  Exception for configuration errors.

- `LLMClientNotConfiguredError`
  
  Exception when client is not configured.

#### Functions

- `configure_llm_client(config: Dict[str, Any]) -> LLMClient`
  
  Configure the global LLM client.
  
  - `config`: LLM configuration dictionary
  - Returns: Configured LLM client

- `get_llm_client() -> LLMClient`
  
  Get the global LLM client.
  
  - Returns: The configured LLM client
  - Raises: `LLMClientNotConfiguredError` if not configured

- `async run_embedded_reasoning(system_prompt: str, user_prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]`
  
  Run embedded reasoning with the language model.
  
  - `system_prompt`: System prompt providing context
  - `user_prompt`: User prompt to process
  - `tools`: Optional list of tools
  - Returns: Dictionary with response and tool calls

### fluent_mcp.core.tool_registry

Module for registering and managing tools.

#### Functions

- `register_embedded_tool(name: Optional[str] = None)`
  
  Decorator to register a function as an embedded tool.
  
  - `name`: Optional name for the tool
  - Returns: Decorated function

- `register_external_tool(name: Optional[str] = None)`
  
  Decorator to register a function as an external tool.
  
  - `name`: Optional name for the tool
  - Returns: Decorated function

- `get_embedded_tool(name: str) -> Optional[Callable]`
  
  Get an embedded tool by name.
  
  - `name`: Name of the tool to retrieve
  - Returns: Tool function or None if not found

- `get_external_tool(name: str) -> Optional[Callable]`
  
  Get an external tool by name.
  
  - `name`: Name of the tool to retrieve
  - Returns: Tool function or None if not found

- `list_embedded_tools() -> List[str]`
  
  List all registered embedded tool names.
  
  - Returns: List of tool names

- `list_external_tools() -> List[str]`
  
  List all registered external tool names.
  
  - Returns: List of tool names

- `get_tools_as_openai_format() -> List[Dict[str, Any]]`
  
  Get embedded tools in OpenAI function calling format.
  
  - Returns: List of tools formatted for OpenAI's API

- `get_external_tools_as_openai_format() -> List[Dict[str, Any]]`
  
  Get external tools in OpenAI function calling format.
  
  - Returns: List of tools formatted for OpenAI's API

- `register_tool(tool: Callable) -> None`
  
  Register a tool function directly.
  
  - `tool`: Tool function to register

- `register_external_tools(tools: List[Callable]) -> None`
  
  Register a list of external tools.
  
  - `tools`: List of tool functions to register

### fluent_mcp.core.prompt_loader

Module for loading and managing prompts.

#### Classes

- `PromptLoader`
  
  Loader for LLM prompts.
  
  - `__init__(prompt_dir: Optional[str] = None)`
    - `prompt_dir`: Directory containing prompt files
  
  - `load_prompt(name: str) -> Optional[str]`
    - `name`: Name of the prompt
    - Returns: Prompt text or None if not found
  
  - `load_template(name: str) -> Optional[Dict[str, Any]]`
    - `name`: Name of the template
    - Returns: Template dictionary or None if not found
  
  - `format_prompt(prompt: str, variables: Dict[str, Any]) -> str`
    - `prompt`: Prompt text
    - `variables`: Variables to substitute
    - Returns: Formatted prompt

- `PromptLoaderError`
  
  Base exception for prompt loader errors.

- `InvalidFrontmatterError`
  
  Exception for invalid frontmatter.

- `MissingRequiredFieldError`
  
  Exception for missing required fields.

#### Functions

- `parse_markdown_with_frontmatter(file_path: str) -> Dict[str, Any]`
  
  Parse a markdown file with YAML frontmatter.
  
  - `file_path`: Path to the markdown file
  - Returns: Dictionary with parsed frontmatter and content
  - Raises: `InvalidFrontmatterError` or `MissingRequiredFieldError`

- `load_prompts(directory: str) -> List[Dict[str, Any]]`
  
  Load prompts from a directory.
  
  - `directory`: Directory containing prompt files
  - Returns: List of prompt dictionaries

### fluent_mcp.core.server

Module for the MCP server implementation.

#### Classes

- `Server`
  
  MCP Server implementation.
  
  - `__init__(config: Dict[str, Any], name: str = "mcp_server", stdin=sys.stdin, stdout=sys.stdout)`
    - `config`: Server configuration
    - `name`: Server name
    - `stdin`: Input stream
    - `stdout`: Output stream
  
  - `register_tool(tool: Any) -> None`
    - `tool`: Tool to register
  
  - `load_prompt(prompt: Any) -> None`
    - `prompt`: Prompt to load
  
  - `read_message() -> Dict[str, Any]`
    - Returns: Parsed message from stdin
  
  - `write_message(message: Dict[str, Any]) -> None`
    - `message`: Message to write to stdout
  
  - `async process_message(message: Dict[str, Any]) -> Dict[str, Any]`
    - `message`: Message to process
    - Returns: Response message
  
  - `run() -> None`
    - Run the server

#### Functions

- `register_embedded_tools(tools: List[Callable]) -> None`
  
  Register embedded tools with the tool registry.
  
  - `tools`: List of tool functions

- `create_mcp_server(server_name: str, embedded_tools=None, external_tools=None, prompts=None, prompts_dir=None, config=None) -> Server`
  
  Create and configure an MCP server.
  
  - `server_name`: Name of the server
  - `embedded_tools`: List of embedded tools
  - `external_tools`: List of external tools
  - `prompts`: List of prompts
  - `prompts_dir`: Directory containing prompt files
  - `config`: Configuration dictionary
  - Returns: Configured server instance

### fluent_mcp.cli

Module for the command-line interface.

#### Functions

- `parse_args(args: Optional[List[str]] = None) -> argparse.Namespace`
  
  Parse command line arguments.
  
  - `args`: Command line arguments
  - Returns: Parsed arguments

- `main(args: Optional[List[str]] = None) -> int`
  
  Main entry point for the CLI.
  
  - `args`: Command line arguments
  - Returns: Exit code

## Configuration Options

### LLM Configuration

```python
{
    "provider": "ollama",  # or "groq"
    "model": "llama2",     # Model name
    "base_url": "http://localhost:11434",  # API endpoint
    "api_key": "your_api_key",  # API key for the provider
    
    # Rate limiting configuration (optional)
    "rate_limits": {
        "requests_per_minute": 5,   # Max requests per minute
        "requests_per_hour": 100,   # Max requests per hour
    },
    
    # Retry configuration (optional)
    "retry_config": {
        "max_retries": 5,          # Maximum number of retries
        "base_delay": 1.0,         # Base delay in seconds for exponential backoff
        "max_delay": 60.0          # Maximum delay in seconds
    }
}
```

### Server Configuration

```python
{
    "host": "localhost",  # Server host
    "port": 8000,         # Server port
    "debug": False        # Debug mode
}
```

## Tool Format

Tools are registered using decorators:

```python
@register_embedded_tool(name="optional_custom_name")
def my_tool(param1: str, param2: int = 42) -> Dict[str, Any]:
    """
    Tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Tool implementation
    return {"result": f"{param1} {param2}"}
```

## Prompt Format

Prompts are defined in Markdown files with YAML frontmatter:

```markdown
---
name: My Prompt
description: Description of the prompt
model: llama2
temperature: 0.3
---

You are an assistant that can help with specific tasks.

Context:
- Use the available tools to solve problems
- Be concise and clear in your responses
```

## Example Workflow

A typical workflow with Fluent MCP:

1. Create a server using `scaffold_server`
2. Define tools with `register_embedded_tool` and `register_external_tool`
3. Configure the LLM client with `configure_llm_client`
4. Create prompt templates in the prompts directory
5. Create the server with `create_mcp_server`
6. Run the server with `server.run()`
7. Use `run_embedded_reasoning` for tool-assisted reasoning

## Error Handling

Fluent MCP provides several exception classes for error handling:

- `LLMClientError`: Base exception for LLM client errors
- `LLMClientConfigError`: For configuration errors
- `LLMClientNotConfiguredError`: When client is not configured
- `PromptLoaderError`: Base exception for prompt loader errors
- `InvalidFrontmatterError`: For invalid frontmatter
- `MissingRequiredFieldError`: For missing required fields

Proper error handling example:

```python
try:
    llm_client = configure_llm_client(config)
    result = await run_embedded_reasoning(system_prompt, user_prompt)
except LLMClientConfigError as e:
    print(f"Configuration error: {e}")
except LLMClientNotConfiguredError:
    print("LLM client is not configured")
except Exception as e:
    print(f"Unexpected error: {e}")
```
