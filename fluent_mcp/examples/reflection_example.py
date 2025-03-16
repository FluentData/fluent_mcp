"""
Example demonstrating the structured reflection loop in Fluent MCP.

This example shows how to use the reflection system with external tools,
specifically demonstrating a web research tool that uses reflection to
iteratively gather and analyze information.
"""

import asyncio
from typing import Dict, List

from fluent_mcp.core.error_handling import MCPError
from fluent_mcp.core.llm_client import LLMClient, configure_llm_client
from fluent_mcp.core.tool_registry import register_embedded_tool, register_external_tool

# Mock LLM client configuration
llm_config = {
    "provider": "mock",
    "model": "mock-model",
    "api_key": "mock-key",
    "temperature": 0.3,
}


# Mock LLM client for demonstration
class MockLLMClient(LLMClient):
    """Mock LLM client for demonstration purposes."""

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict:
        """Mock chat completion that simulates tool usage."""
        # Simulate the LLM using tools in sequence
        if tools and isinstance(tools, list):
            # First call: Search for information
            return {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "search_web", "arguments": {"query": "artificial intelligence ethics"}},
                    }
                ]
            }
        else:
            # Final call: Complete the task
            return {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "job_complete",
                            "arguments": {
                                "result": "# Research Report: AI Ethics\n\n## Executive Summary\nThis report covers key aspects of AI ethics...\n\n## Key Findings\n1. Ethical considerations in AI development\n2. Impact on society\n3. Regulatory frameworks\n\n## References\n- Source 1\n- Source 2"
                            },
                        },
                    }
                ]
            }


@register_embedded_tool()
async def search_web(query: str) -> List[Dict]:
    """
    Search the web for information about a query.

    Args:
        query: The search query

    Returns:
        A list of search results
    """
    print(f"Searching web for: {query}")
    # In a real implementation, this would call a search API
    return [
        {"title": "AI Ethics Guidelines", "snippet": f"Key principles for ethical AI development"},
        {"title": "Impact of AI on Society", "snippet": f"Analysis of AI's societal implications"},
        {"title": "AI Regulation Framework", "snippet": f"Current and proposed AI regulations"},
    ]


@register_embedded_tool()
async def extract_information(url: str) -> Dict:
    """
    Extract detailed information from a URL.

    Args:
        url: The URL to extract information from

    Returns:
        A dictionary of extracted information
    """
    print(f"Extracting information from: {url}")
    # In a real implementation, this would fetch and parse the URL
    return {
        "title": "AI Ethics Guidelines",
        "content": "Detailed guidelines for ethical AI development...",
        "facts": ["AI systems should be transparent", "Privacy must be protected", "Bias should be minimized"],
    }


@register_external_tool(use_reflection=True, reflection_budget=7)
async def web_research(
    topic: str, task: str = "Research this topic and provide a comprehensive report", llm_client: LLMClient = None
) -> str:
    """
    Research a topic on the web and provide a comprehensive report.

    This tool uses the structured reflection loop to iteratively gather and analyze
    information about a topic from the web. The reflection system handles:
    1. Searching for relevant information
    2. Extracting key details
    3. Synthesizing findings
    4. Formatting the final report

    Args:
        topic: The topic to research
        task: The specific research task description
        llm_client: The LLM client to use for reflection

    Returns:
        A comprehensive research report formatted according to the templates
    """
    print(f"Starting web research on: {topic}")
    # The actual implementation is minimal because the reflection system
    # handles the iterative process of gathering and analyzing information
    return f"Research report on {topic} (handled by reflection)"


async def main():
    """Run the example demonstration."""
    try:
        # Configure and create the mock LLM client
        configure_llm_client(llm_config)
        llm_client = MockLLMClient(llm_config)

        # Run the web_research tool
        topic = "artificial intelligence ethics"
        print(f"\nResearching topic: {topic}\n")

        result = await web_research(
            topic=topic,
            task=f"Research {topic} and create a comprehensive report with key findings and references",
            llm_client=llm_client,
        )

        print("\nResearch Result:\n")
        print(result)

    except MCPError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
