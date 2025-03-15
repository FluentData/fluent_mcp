# Fluent MCP Architecture

This document describes the architecture of Fluent MCP, explaining how the different components work together to create a flexible and powerful framework for building MCP servers.

## System Overview

Fluent MCP is structured around several core components that work together to provide a complete framework for building MCP servers with intelligent reasoning capabilities:

![Architecture Diagram](https://i.imgur.com/example.png)

*Note: The above diagram is a placeholder. Replace with an actual architecture diagram if available.*

## Core Components

### 1. LLM Client

**Purpose**: Provides a standardized interface for communicating with different language model providers.

**Key Features**:
- Supports multiple LLM providers (Ollama, Groq, etc.)
- Handles authentication and API communication
- Provides a unified interface for chat completions
- Manages tool calls made by language models

**Implementation**:
- Located in `fluent_mcp/core/llm_client.py`
- The `LLMClient` class is the main implementation
- Configuration is handled through the `configure_llm_client` function
- A global client instance is maintained for easy access

### 2. Tool Registry

**Purpose**: Manages the registration and discovery of tools that can be used by LLMs.

**Key Features**:
- Supports both embedded tools (used by LLMs) and external tools
- Provides decorators for easy tool registration
- Converts tools to OpenAI function calling format
- Handles parameter type inference and documentation

**Implementation**:
- Located in `fluent_mcp/core/tool_registry.py`
- Uses decorators (`register_embedded_tool`, `register_external_tool`) for registration
- Maintains global registries for both tool types
- Provides functions for discovering and retrieving tools

### 3. Prompt Loader

**Purpose**: Loads and manages prompt templates and configurations.

**Key Features**:
- Loads prompts from markdown files with YAML frontmatter
- Supports prompt variables and substitution
- Validates prompt configurations and requirements
- Organizes prompts by name and purpose

**Implementation**:
- Located in `fluent_mcp/core/prompt_loader.py`
- The `PromptLoader` class handles loading and formatting
- Supports parsing markdown files with frontmatter
- Validates required fields and structure

### 4. Server

**Purpose**: Provides the core server implementation for handling messages and managing the server lifecycle.

**Key Features**:
- Processes messages from stdin/stdout
- Registers and manages tools and prompts
- Manages the server lifecycle (startup, running, shutdown)
- Handles tool execution and responses

**Implementation**:
- Located in `fluent_mcp/core/server.py`
- The `Server` class is the main implementation
- Uses async/await pattern for handling requests
- Supports custom lifecycle management

### 5. Scaffolder

**Purpose**: Generates new MCP server projects with the proper structure and configuration.

**Key Features**:
- Creates directory structure for new servers
- Generates initial configuration files
- Sets up basic tool and prompt organization
- Creates starter implementation files

**Implementation**:
- Located in `fluent_mcp/scaffolder.py`
- Functions for creating directories and files
- Template-based file generation

### 6. CLI

**Purpose**: Provides a command-line interface for managing MCP servers.

**Key Features**:
- Creates new server projects
- Manages server lifecycle
- Handles configuration loading
- Provides user-friendly commands

**Implementation**:
- Located in `fluent_mcp/cli.py`
- Uses argparse for command-line argument parsing
- Connects to scaffolder for project generation

## Data Flow

### 1. Server Creation

1. User calls `scaffold_server` or uses CLI to create a new server
2. Scaffolder generates the project structure and initial files
3. User adds custom tools and prompts to the server

### 2. Server Configuration

1. User configures the LLM client with provider details
2. Tools are registered using decorators
3. Prompts are loaded from the prompts directory
4. Server is created with `create_mcp_server`

### 3. Server Execution

1. Server's `run` method is called to start processing
2. Server listens for messages on stdin
3. Messages are processed and responses sent to stdout

### 4. Embedded Reasoning

1. `run_embedded_reasoning` is called with prompts
2. LLM client sends request to the LLM provider
3. LLM makes tool calls based on the user's query
4. Tool calls are executed and results returned

## Design Principles

Fluent MCP is designed with the following principles in mind:

1. **Simplicity**: Make it easy to create and run MCP servers
2. **Flexibility**: Support multiple LLM providers and tool types
3. **Extensibility**: Allow easy extension with custom tools
4. **Modularity**: Keep components separate with clear interfaces
5. **Robustness**: Handle errors gracefully and provide helpful feedback

## Extensibility

Fluent MCP is designed to be extended in several ways:

### Adding New LLM Providers

To add support for a new LLM provider:

1. Update the `LLMClient` class to support the new provider
2. Add validation for provider-specific configuration
3. Implement the chat completion method for the provider

### Creating Custom Tools

Custom tools can be created by:

1. Defining a function with appropriate type annotations
2. Decorating it with `register_embedded_tool` or `register_external_tool`
3. Providing clear documentation in the docstring

### Enhancing Server Behavior

Server behavior can be customized by:

1. Extending the `Server` class with custom methods
2. Overriding the `process_message` method for custom processing
3. Implementing a custom lifespan context manager

## Future Architecture Directions

The architecture of Fluent MCP is designed to evolve in the following directions:

1. **Self-extending Tools**: Enable LLMs to create and register their own tools
2. **Distributed Tool Execution**: Support for distributed tool execution across multiple servers
3. **Tool Composition**: Allow tools to be composed for complex operations
4. **Reasoning Patterns**: Built-in support for common reasoning patterns
5. **Performance Optimization**: Optimize tool execution and LLM communication
6. **Security Enhancements**: Improved security for tool execution

## Component Interactions

### LLM Client and Tool Registry

- The LLM client uses the tool registry to get tools in OpenAI format
- Tool calls from the LLM are matched with registered tools for execution

### Server and LLM Client

- The server configures the LLM client based on server configuration
- The server uses the LLM client for embedded reasoning

### Prompt Loader and Server

- The server loads prompts using the prompt loader
- Prompts are made available for use in embedded reasoning

### Scaffolder and Server

- The scaffolder creates the initial structure for a server
- The structure follows conventions expected by the server implementation

## Implementation Details

### Asynchronous Processing

Fluent MCP uses async/await patterns for efficient handling of I/O-bound operations:

- LLM API requests are handled asynchronously
- Server message processing is asynchronous
- Tool execution can be synchronous or asynchronous

### Type Annotations

Type annotations are used throughout the codebase for:

- Documentation of interfaces
- Tool parameter and return type inference
- Static type checking
- Generation of OpenAI function schemas

### Error Handling

A consistent approach to error handling is used:

- Custom exception classes for different error types
- Proper exception propagation
- Detailed error messages for debugging
- Graceful degradation when possible

### Tool Registration

Tool registration follows a decorator pattern:

1. User defines a function with type annotations
2. Function is decorated with `@register_embedded_tool()` or `@register_external_tool()`
3. Tool is added to the appropriate registry
4. Tool's docstring and type annotations are used for metadata

### Embedded Reasoning Workflow

The embedded reasoning workflow follows these steps:

1. User provides system and user prompts
2. `run_embedded_reasoning` is called with these prompts
3. Available tools are gathered from the tool registry
4. Tools are converted to OpenAI function calling format
5. Request is sent to the LLM provider
6. LLM response with tool calls is processed
7. Results are returned to the caller

## MCP Protocol Implementation

The Model Context Protocol (MCP) is implemented through:

1. **Message Format**: Standardized JSON format for messages
2. **Tool Registration**: Consistent way to register tools
3. **Tool Execution**: Protocol for executing tools and returning results
4. **Lifecycle Management**: Server lifecycle follows the protocol

## Self-Improving AI Systems

Fluent MCP is designed with self-improving AI systems in mind:

1. **Tool Creation**: LLMs can potentially generate code for new tools
2. **Dynamic Registration**: Tools can be registered at runtime
3. **Feedback Loop**: Results from tool execution can inform further development
4. **Extensible Architecture**: The system is designed to be extended by AI systems
5. **Tool Composition**: Complex capabilities can be built from simple tools

## Security Considerations

Security is important in tool-using AI systems:

1. **Validation**: Input validation for all tool parameters
2. **Sandboxing**: Tools should run in a restricted environment
3. **Permission Model**: Future versions may include a permission model for tools
4. **Audit Trails**: Logging of all tool executions for auditing
5. **Rate Limiting**: Protection against excessive tool usage

## Performance Considerations

The architecture addresses performance through:

1. **Asynchronous Processing**: Non-blocking I/O operations
2. **Efficient Tool Execution**: Tools execute only when needed
3. **Connection Pooling**: Reuse connections to LLM providers
4. **Lazy Loading**: Prompts and tools are loaded on demand
5. **Caching**: Potential for caching common results

## Conclusion

The Fluent MCP architecture provides a flexible, extensible framework for building MCP servers. Its modular design allows for easy customization and extension, making it suitable for a wide range of applications including self-improving AI systems.

The clear separation of concerns between LLM clients, tool registration, prompt loading, and server management allows developers to focus on creating powerful tools and prompts without worrying about the underlying infrastructure.

Future development will focus on enhancing the self-improving capabilities, performance optimization, and security enhancements, making Fluent MCP an even more powerful foundation for AI-powered applications.
