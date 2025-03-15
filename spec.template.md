---
server_name: example_server
description: "A specialized MCP server for example purposes"
version: "0.1.0"
llm_provider: "ollama"  # options: "ollama", "groq", etc.
llm_model: "llama2"
required_tools:
  - name: "search_documents"
    description: "Search through document collection"
    type: "embedded"  # options: "embedded", "external"
  - name: "process_data"
    description: "Process data in various formats"
    type: "embedded"
  - name: "generate_report"
    description: "Generate a formatted report"
    type: "external"
---

# Example Server Specification

This document provides detailed specifications for the Example MCP server implementation.

## Overview

The Example Server is designed to [describe the specific purpose and functionality of your server]. It leverages the Fluent MCP framework to provide [key capabilities].

## Tools

### search_documents

This tool searches through a collection of documents to find relevant information.

**Input Parameters:**
- `query` (string): The search query
- `max_results` (int, optional): Maximum number of results to return (default: 10)
- `filter_criteria` (dict, optional): Additional filtering criteria

**Output:**
- A list of document matches with relevance scores

**Implementation Details:**
```python
@register_embedded_tool()
def search_documents(query: str, max_results: int = 10, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Search through document collection.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        filter_criteria: Additional filtering criteria
        
    Returns:
        A list of document matches with relevance scores
    """
    # Implementation details here
    # ...
```

### process_data

This tool processes data in various formats (CSV, JSON, etc.).

**Input Parameters:**
- `data` (string or dict): The data to process
- `format` (string): The format of the data (csv, json, etc.)
- `options` (dict, optional): Processing options

**Output:**
- The processed data in the requested format

**Implementation Details:**
```python
@register_embedded_tool()
def process_data(data: Union[str, Dict[str, Any]], format: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process data in various formats.
    
    Args:
        data: The data to process
        format: The format of the data (csv, json, etc.)
        options: Processing options
        
    Returns:
        The processed data
    """
    # Implementation details here
    # ...
```

### generate_report

This tool generates a formatted report based on provided data.

**Input Parameters:**
- `data` (dict): The data to include in the report
- `template` (string, optional): The report template to use
- `format` (string, optional): Output format (pdf, html, markdown)

**Output:**
- The generated report in the requested format

**Implementation Details:**
```python
@register_external_tool()
def generate_report(data: Dict[str, Any], template: Optional[str] = "default", format: str = "markdown") -> str:
    """
    Generate a formatted report.
    
    Args:
        data: The data to include in the report
        template: The report template to use
        format: Output format (pdf, html, markdown)
        
    Returns:
        The generated report
    """
    # Implementation details here
    # ...
```

## Prompts

### System Prompt

The system prompt should establish the server's purpose and capabilities:

```
You are an AI assistant integrated with the Example MCP server. Your purpose is to help users [specific purpose].

You have access to the following tools:
- search_documents: Search through document collection
- process_data: Process data in various formats
- generate_report: Generate a formatted report

Please help users by [specific guidance on how to help users].
```

### User Interaction Prompt

Template for handling user queries:

```
User query: {{user_query}}

Please respond by:
1. Analyzing the query to understand the user's intent
2. Using the appropriate tools to gather necessary information
3. Providing a clear, helpful response based on the tool results
4. Suggesting next steps or additional information if relevant
```

## Additional Requirements

### Error Handling

- Implement robust error handling for all tools
- Provide meaningful error messages to users
- Log detailed error information for debugging

### Security Considerations

- Validate all user inputs before processing
- Implement proper authentication for external tools
- Ensure sensitive information is not exposed in logs or responses

### Performance Requirements

- Tools should respond within reasonable timeframes (specify if there are specific SLAs)
- Implement caching where appropriate to improve performance
- Consider rate limiting for external API calls

### Deployment

- The server should be deployable as a Docker container
- Provide environment variable configuration for all sensitive settings
- Include health check endpoints for monitoring

## References

- [Link to relevant documentation or resources]
- [Additional reference material]