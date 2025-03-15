# MCP Server Implementation Instructions

This document provides step-by-step instructions for implementing a Model Context Protocol (MCP) server using the Fluent MCP framework. Follow these steps in order.

## Step 1: Review Project Specification

1. Read the `spec.md` file thoroughly to understand the specific requirements for this MCP server
2. Identify all required tools, prompts, and configuration settings
3. Note any special requirements or integrations

## Step 2: Scaffold the Project

Create the initial project structure using the Fluent MCP CLI:

```bash
# If you're already in a directory with only instructions.md and spec.md, 
# this will scaffold in the current directory
fluent-mcp new .
```

## Step 3: Configure Environment Variables

1. Copy the `.env.example` file to `.env`
2. Update the environment variables based on the requirements in `spec.md`
3. Ensure all required API keys and configuration values are set

## Step 4: Implement Tools

Based on the tools specified in `spec.md`:

1. Create tool functions in the `tools/` directory
2. Use the `@register_embedded_tool()` decorator for tools that need to be available to the LLM
3. Use the `@register_external_tool()` decorator for tools that should be exposed through the MCP server
4. Implement each tool according to its specification, including proper type hints and docstrings
5. Test each tool individually to ensure it works as expected

## Step 5: Create Prompts

1. Add all required prompt templates to the `prompts/` directory
2. Use YAML frontmatter for metadata and variables
3. Ensure prompts follow the best practices defined in `spec.md`

## Step 6: Configure the Server

1. Update the `main.py` file to properly configure the server based on `spec.md`
2. Ensure all tools are properly registered
3. Configure the LLM provider and model
4. Set up proper error handling and logging

## Step 7: Add Tests

1. Create appropriate tests for all tools and key functionality
2. Include integration tests for the server itself
3. Ensure tests cover error cases and edge conditions

## Step 8: Update Documentation

1. Update the project README.md with:
   - Project description
   - Setup instructions
   - Available tools
   - Configuration options
   - Example usage

## Step 9: Review Implementation

1. Check that all requirements from `spec.md` are implemented
2. Verify that code follows best practices:
   - Proper error handling
   - Comprehensive logging
   - Appropriate type hints
   - Clean, documented code
3. Run all tests to ensure functionality

## Step 10: Prepare for Deployment

1. Verify that the server can be run with `python main.py`
2. Document any deployment-specific requirements
3. Ensure all dependencies are properly listed in requirements files

## Additional Guidelines

- Follow the Fluent MCP patterns and structure
- Maintain clear separation between tools, prompts, and server configuration
- Use type hints consistently for better code quality
- Document all functions, classes, and modules
- Log important events and errors
- Handle errors gracefully with appropriate user feedback

Remember to refer to the `spec.md` file for detailed requirements specific to this MCP server implementation.