"""
Example of an external tool that leverages embedded reasoning in Fluent MCP.

This script demonstrates how to implement an external tool that uses embedded reasoning
to perform complex multi-step tasks while presenting a simple interface to consuming LLMs.

IMPORTANT: This pattern demonstrates a key architectural approach in Fluent MCP:
1. External tools (exposed to consuming LLMs) can be simple interfaces to complex functionality
2. Embedded reasoning can be used within external tools to perform multi-step reasoning
3. Embedded tools (hidden from consuming LLMs) can be used by the embedded reasoning engine
   to perform the actual work

This approach has several benefits:
- Reduces token usage in the consuming LLM by offloading complex reasoning to the embedded LLM
- Provides a simpler interface to consuming LLMs, making them easier to use
- Allows for more complex functionality to be implemented without exposing implementation details
- Enables better separation of concerns between the consuming LLM and the embedded reasoning
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fluent_mcp import create_mcp_server
from fluent_mcp.core.llm_client import run_embedded_reasoning
from fluent_mcp.core.tool_registry import (
    get_embedded_tool,
    get_external_tool,
    list_embedded_tools,
    list_external_tools,
    register_embedded_tool,
    register_external_tool,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reasoning_external_tool_example")


# Define some embedded tools that will only be used by the embedded LLM
# These tools are NOT exposed to consuming LLMs
@register_embedded_tool()
def search_web(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the web for information related to a query.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        A list of search results with title, url, and snippet
    """
    # This is a mock implementation
    logger.info(f"[EMBEDDED] Searching web for: {query} (max results: {max_results})")

    # In a real implementation, you would use a search API
    mock_results = [
        {
            "title": f"Result 1 for {query}",
            "url": f"https://example.com/result1?q={query}",
            "snippet": f"This is the first result for {query}. It contains relevant information about the topic.",
        },
        {
            "title": f"Result 2 for {query}",
            "url": f"https://example.com/result2?q={query}",
            "snippet": f"This is the second result for {query}. It provides additional context and details.",
        },
        {
            "title": f"Result 3 for {query}",
            "url": f"https://example.com/result3?q={query}",
            "snippet": f"This is the third result for {query}. It offers a different perspective on the topic.",
        },
        {
            "title": f"Result 4 for {query}",
            "url": f"https://example.com/result4?q={query}",
            "snippet": f"This is the fourth result for {query}. It includes more specialized information.",
        },
    ]

    return mock_results[:max_results]


@register_embedded_tool()
def extract_information(text: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract structured information from text.

    Args:
        text: The text to extract information from
        focus_areas: Optional list of specific areas to focus on

    Returns:
        A dictionary containing extracted information
    """
    # This is a mock implementation
    logger.info(f"[EMBEDDED] Extracting information from text (focus areas: {focus_areas})")

    # In a real implementation, you would use NLP techniques or an LLM
    focus_areas = focus_areas or ["general", "facts", "dates"]

    # Create a mock extraction based on the text and focus areas
    extraction = {
        "general_topic": f"Information about {text.split()[0] if text else 'unknown'}",
        "key_points": [f"Key point 1 related to {area}" for area in focus_areas],
        "entities": [{"name": f"Entity {i}", "type": "concept", "relevance": 0.9 - (i * 0.1)} for i in range(1, 4)],
    }

    return extraction


@register_embedded_tool()
def summarize_content(content: List[Dict[str, Any]], max_length: int = 200) -> str:
    """
    Summarize a collection of content items.

    Args:
        content: List of content items to summarize
        max_length: Maximum length of the summary in characters

    Returns:
        A concise summary of the content
    """
    # This is a mock implementation
    logger.info(f"[EMBEDDED] Summarizing {len(content)} content items (max length: {max_length})")

    # In a real implementation, you would use an LLM or summarization algorithm

    # Create a mock summary based on the content
    items_text = []
    for item in content:
        if isinstance(item, dict):
            if "title" in item and "snippet" in item:
                items_text.append(f"{item['title']}: {item['snippet']}")
            elif "general_topic" in item and "key_points" in item:
                points = ", ".join(item["key_points"][:2])
                items_text.append(f"{item['general_topic']} - {points}")
            else:
                items_text.append(str(item)[:50] + "...")
        else:
            items_text.append(str(item)[:50] + "...")

    combined = " ".join(items_text)
    summary = f"Summary of research findings: {combined[:max_length-30]}..."

    return summary


# Define an external tool that uses embedded reasoning
# This tool IS exposed to consuming LLMs
@register_external_tool()
async def research_assistant(question: str, depth: int = 2) -> Dict[str, Any]:
    """
    Research a question and provide a comprehensive answer.

    This tool performs in-depth research on a given question by searching for information,
    extracting key details, and synthesizing a comprehensive answer.

    Args:
        question: The research question to investigate
        depth: The depth of research (1-3, higher means more thorough)

    Returns:
        A dictionary containing the research results, including a summary and sources
    """
    logger.info(f"[EXTERNAL] Research assistant invoked for question: {question} (depth: {depth})")

    # This is where the magic happens - we use embedded reasoning to perform the research
    # The consuming LLM only sees the simple interface, but internally we're using
    # a complex reasoning process with multiple tool calls

    # Define the system prompt for the embedded reasoning
    system_prompt = """
    You are a research assistant that helps answer questions by searching for information,
    extracting key details, and synthesizing comprehensive answers.
    
    You have access to several tools:
    1. search_web: Search the web for information
    2. extract_information: Extract structured information from text
    3. summarize_content: Summarize a collection of content
    
    Follow these steps to research a question:
    1. Search for relevant information using search_web
    2. Extract key information from the search results using extract_information
    3. If needed, perform additional searches based on what you've learned
    4. Synthesize the information into a comprehensive answer using summarize_content
    5. Include sources and citations in your response
    
    Be thorough and make sure to explore the topic from multiple angles.
    """

    # Define the user prompt (the research question)
    user_prompt = f"""
    Research the following question with a depth of {depth} (1-3, higher means more thorough):
    
    {question}
    
    Provide a comprehensive answer with sources.
    """

    # Run the embedded reasoning process
    # This will allow the embedded LLM to make multiple tool calls to the embedded tools
    logger.info(f"[EXTERNAL] Starting embedded reasoning process for research")
    result = await run_embedded_reasoning(system_prompt, user_prompt)

    # Check if the reasoning was successful
    if result["status"] != "complete" or result["error"]:
        logger.error(f"[EXTERNAL] Embedded reasoning failed: {result['error']}")
        return {
            "status": "error",
            "question": question,
            "answer": "Failed to complete research due to an error in the reasoning process.",
            "error": result["error"],
        }

    # Extract the research results from the embedded reasoning
    # In a real implementation, you would parse the result more carefully
    # and possibly do additional processing

    # For this example, we'll create a structured response based on the embedded reasoning result
    research_result = {
        "status": "success",
        "question": question,
        "answer": result["content"],
        "tool_calls_made": len(result["tool_calls"]),
        "depth": depth,
        "sources": [
            {"title": f"Source {i+1}", "url": f"https://example.com/source{i+1}"} for i in range(min(depth + 1, 5))
        ],
    }

    logger.info(f"[EXTERNAL] Research completed with {research_result['tool_calls_made']} embedded tool calls")

    return research_result


async def main():
    """Main entry point."""
    logger.info("Reasoning External Tool Example")

    # List all registered tools
    embedded_tools = list_embedded_tools()
    external_tools = list_external_tools()

    logger.info(f"Registered embedded tools (hidden from consuming LLMs): {', '.join(embedded_tools)}")
    logger.info(f"Registered external tools (exposed to consuming LLMs): {', '.join(external_tools)}")

    # Demonstrate the research_assistant external tool
    logger.info("\n=== Demonstrating the research_assistant external tool ===\n")

    research_tool = get_external_tool("research_assistant")
    if research_tool:
        try:
            # Use the research_assistant tool to answer a question
            question = "What are the key benefits of using embedded reasoning in AI systems?"
            logger.info(f"Asking research question: {question}")

            # Call the research_assistant tool
            # This will trigger the embedded reasoning process internally
            result = await research_tool(question, depth=2)

            # Display the result
            logger.info(f"Research result: {json.dumps(result, indent=2)}")

            # Explain the benefits of this approach
            logger.info("\n=== Benefits of this approach ===\n")
            logger.info("1. Token Efficiency: The consuming LLM only needs to understand a simple interface")
            logger.info("   instead of all the complex reasoning steps, saving tokens.")
            logger.info("2. Complexity Hiding: The complex multi-step reasoning is hidden from the consuming LLM,")
            logger.info("   making it easier to use and less prone to errors.")
            logger.info("3. Separation of Concerns: The embedded reasoning engine handles the complex logic,")
            logger.info("   while the consuming LLM focuses on higher-level tasks.")
            logger.info("4. Reusability: The embedded tools can be reused across multiple external tools,")
            logger.info("   making it easier to build complex functionality.")

        except Exception as e:
            logger.error(f"Error demonstrating research_assistant: {str(e)}")
    else:
        logger.error("research_assistant tool not found")

    # Create an MCP server with the registered tools
    logger.info("\n=== Creating MCP server with registered tools ===\n")

    # Get all the tool functions
    embedded_tool_funcs = [get_embedded_tool(name) for name in embedded_tools]
    external_tool_funcs = [get_external_tool(name) for name in external_tools]

    # Create the server
    server = create_mcp_server(
        server_name="reasoning_example_server",
        embedded_tools=embedded_tool_funcs,  # These tools will ONLY be available to the embedded LLM
        external_tools=external_tool_funcs,  # These tools will be exposed to consuming LLMs
        config={
            "debug": True,
            # Add LLM config if needed
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",  # Dummy value for Ollama
        },
    )

    logger.info("Server created successfully")
    logger.info("In a real application, you would call server.run() here")
    logger.info("When the server runs:")
    logger.info("- Embedded tools (search_web, extract_information, summarize_content) will ONLY")
    logger.info("  be available to the embedded LLM, not to consuming LLMs")
    logger.info("- External tools (research_assistant) will be exposed to consuming LLMs")
    logger.info("- When a consuming LLM calls research_assistant, it will trigger embedded")
    logger.info("  reasoning that can use the embedded tools to perform complex tasks")


if __name__ == "__main__":
    asyncio.run(main())
