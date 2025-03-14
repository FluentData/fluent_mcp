"""
Example script demonstrating the use of embedded reasoning.

This script shows how to:
1. Register embedded tools
2. Configure the LLM client
3. Run embedded reasoning with the tools
4. Process the results and execute tool calls
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock

from fluent_mcp.core.llm_client import (
    configure_llm_client,
    get_llm_client,
    run_embedded_reasoning,
    LLMClient
)
from fluent_mcp.core.tool_registry import (
    register_embedded_tool,
    list_embedded_tools,
    get_tools_as_openai_format
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedded_reasoning_example")

# Define and register some embedded tools
@register_embedded_tool()
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

@register_embedded_tool()
def calculate_product(numbers: List[float]) -> float:
    """Calculate the product of a list of numbers."""
    result = 1
    for num in numbers:
        result *= num
    return result

@register_embedded_tool()
def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

@register_embedded_tool()
def get_weather(location: str, units: str = "metric") -> Dict[str, Any]:
    """Get the current weather for a location.
    
    Args:
        location: The city or location to get weather for
        units: The units to use (metric or imperial)
        
    Returns:
        A dictionary with weather information
    """
    # This is a mock implementation
    logger.info(f"Getting weather for {location} in {units} units")
    
    # In a real implementation, you would call a weather API
    mock_weather = {
        "location": location,
        "temperature": 22 if units == "metric" else 72,
        "condition": "Sunny",
        "humidity": 65,
        "wind_speed": 10 if units == "metric" else 6.2,
        "units": units
    }
    
    return mock_weather

# Create a mock LLM client for demonstration purposes
class MockLLMClient(LLMClient):
    """A mock LLM client for demonstration purposes."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the mock client."""
        self.logger = logging.getLogger("fluent_mcp.llm_client")
        self.provider = config.get("provider", "mock")
        self.model = config.get("model", "mock-model")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.api_key = config.get("api_key", "mock-key")
        self._client = None
        self.logger.info(f"Initialized mock LLM client with model {self.model}")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             tools: Optional[List[Dict[str, Any]]] = None, 
                             temperature: float = 0.3, 
                             max_tokens: int = 1000) -> Dict[str, Any]:
        """Mock implementation of chat completion."""
        self.logger.info(f"Mock chat completion with {len(messages)} messages")
        
        # Extract the user message
        user_message = next((m["content"] for m in messages if m["role"] == "user"), "")
        
        # Prepare a mock response based on the user message
        if "calculate" in user_message.lower() or "numbers" in user_message.lower():
            # For math-related queries
            return {
                "status": "complete",
                "content": "I'll help you calculate these values using the available tools.",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "calculate_sum",
                            "arguments": {"numbers": [5, 10, 15, 20, 25]}
                        }
                    },
                    {
                        "id": "call_124",
                        "type": "function",
                        "function": {
                            "name": "calculate_product",
                            "arguments": {"numbers": [5, 10, 15, 20, 25]}
                        }
                    },
                    {
                        "id": "call_125",
                        "type": "function",
                        "function": {
                            "name": "calculate_average",
                            "arguments": {"numbers": [5, 10, 15, 20, 25]}
                        }
                    }
                ],
                "error": None
            }
        elif "weather" in user_message.lower():
            # For weather-related queries
            return {
                "status": "complete",
                "content": "I'll check the weather information for you.",
                "tool_calls": [
                    {
                        "id": "call_126",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"location": "New York", "units": "metric"}
                        }
                    },
                    {
                        "id": "call_127",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": {"location": "London", "units": "imperial"}
                        }
                    }
                ],
                "error": None
            }
        else:
            # Default response
            return {
                "status": "complete",
                "content": "I'm not sure how to help with that specific request.",
                "tool_calls": [],
                "error": None
            }

async def run_example():
    """Run the embedded reasoning example."""
    # Configure the LLM client
    config = {
        "provider": "mock",
        "model": "mock-model"
    }
    
    try:
        # Patch the LLMClient to use our MockLLMClient
        with patch('fluent_mcp.core.llm_client.LLMClient', MockLLMClient):
            configure_llm_client(config)
            client = get_llm_client()
            logger.info(f"Configured LLM client with provider: {client.provider}, model: {client.model}")
            
            # List registered tools
            tools = list_embedded_tools()
            logger.info(f"Registered tools: {', '.join(tools)}")
            
            # Get tools in OpenAI format
            openai_tools = get_tools_as_openai_format()
            logger.info(f"Number of tools in OpenAI format: {len(openai_tools)}")
            
            # Example 1: Math calculation
            logger.info("\n--- Example 1: Math Calculation ---")
            system_prompt = """You are a helpful assistant that can perform calculations.
            Use the provided tools to solve math problems."""
            
            user_prompt = """I have the following numbers: 5, 10, 15, 20, and 25.
            Can you calculate their sum, product, and average?"""
            
            result = await run_embedded_reasoning(system_prompt, user_prompt)
            
            if result["status"] == "complete":
                logger.info(f"Response: {result['content']}")
                
                # Process tool calls
                for tool_call in result["tool_calls"]:
                    if tool_call["type"] == "function":
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]
                        
                        logger.info(f"Tool call: {function_name}({arguments})")
                        
                        # Execute the tool call
                        if function_name in tools:
                            tool_fn = globals()[function_name]  # Get the function from globals
                            tool_result = tool_fn(**arguments)
                            logger.info(f"Tool result: {tool_result}")
            else:
                logger.error(f"Error: {result['error']}")
            
            # Example 2: Weather information
            logger.info("\n--- Example 2: Weather Information ---")
            system_prompt = """You are a helpful assistant that can provide weather information.
            Use the provided tools to get weather data."""
            
            user_prompt = """What's the current weather in New York? 
            Also, can you tell me the weather in London in imperial units?"""
            
            result = await run_embedded_reasoning(system_prompt, user_prompt)
            
            if result["status"] == "complete":
                logger.info(f"Response: {result['content']}")
                
                # Process tool calls
                for tool_call in result["tool_calls"]:
                    if tool_call["type"] == "function":
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]
                        
                        logger.info(f"Tool call: {function_name}({arguments})")
                        
                        # Execute the tool call
                        if function_name in tools:
                            tool_fn = globals()[function_name]  # Get the function from globals
                            tool_result = tool_fn(**arguments)
                            logger.info(f"Tool result: {json.dumps(tool_result, indent=2)}")
            else:
                logger.error(f"Error: {result['error']}")
                
    except Exception as e:
        logger.exception(f"Error in example: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_example()) 