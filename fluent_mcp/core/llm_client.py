"""
LLM client implementation.

This module provides a client for interacting with language models
from various providers.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

# Global client instance
_llm_client = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMClientConfigError(LLMClientError):
    """Exception raised for configuration errors."""

    pass


class LLMClientNotConfiguredError(LLMClientError):
    """Exception raised when the client is not configured."""

    pass


class LLMClient:
    """
    Client for interacting with language models.

    Supports multiple providers and models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize a new LLM client.

        Args:
            config: LLM configuration
        """
        self.logger = logging.getLogger("fluent_mcp.llm_client")

        # Validate required configuration
        required_fields = ["provider", "model"]
        missing_fields = [field for field in required_fields if not config.get(field)]

        if missing_fields:
            error_msg = f"Missing required configuration fields: {', '.join(missing_fields)}"
            self.logger.error(error_msg)
            raise LLMClientConfigError(error_msg)

        self.provider = config.get("provider").lower()
        self.model = config.get("model")
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")

        # Validate provider-specific requirements
        if self.provider == "ollama":
            if not self.base_url:
                # Default Ollama base URL
                self.base_url = "http://localhost:11434"
                self.logger.info(f"Using default Ollama base URL: {self.base_url}")
            # For Ollama, api_key can be a dummy value
            if not self.api_key:
                self.api_key = "ollama"
        elif self.provider == "groq":
            if not self.api_key:
                error_msg = "API key is required for Groq provider"
                self.logger.error(error_msg)
                raise LLMClientConfigError(error_msg)
        else:
            error_msg = f"Unsupported provider: {self.provider}. Supported providers are: ollama, groq"
            self.logger.error(error_msg)
            raise LLMClientConfigError(error_msg)

        # Initialize the client based on the provider
        self._client = self._initialize_client()

    def _initialize_client(self):
        """
        Initialize the provider-specific client.

        Returns:
            The initialized client
        """
        try:
            if self.provider == "ollama":
                from openai import OpenAI

                client = OpenAI(base_url=self.base_url, api_key=self.api_key)
                self.logger.info(f"Initialized Ollama client with model {self.model}")
                return client
            elif self.provider == "groq":
                from openai import OpenAI

                client = OpenAI(
                    base_url=("https://api.groq.com/openai/v1" if not self.base_url else self.base_url),
                    api_key=self.api_key,
                )
                self.logger.info(f"Initialized Groq client with model {self.model}")
                return client
        except ImportError as e:
            error_msg = f"Failed to import required package for {self.provider}: {str(e)}"
            self.logger.error(error_msg)
            raise LLMClientConfigError(error_msg)
        except Exception as e:
            error_msg = f"Failed to initialize {self.provider} client: {str(e)}"
            self.logger.error(error_msg)
            raise LLMClientConfigError(error_msg)

    async def generate(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text from the language model.

        Args:
            prompt: The prompt to send to the model
            options: Additional options for the generation

        Returns:
            The generated text
        """
        # TODO: Implement generation logic
        options = options or {}

        print(f"Generating with {self.provider}/{self.model}: {prompt[:50]}...")
        return f"Generated response for: {prompt[:20]}..."

    async def chat(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chat with the language model.

        Args:
            messages: List of messages in the conversation
            options: Additional options for the chat

        Returns:
            The model's response
        """
        # TODO: Implement chat logic
        options = options or {}

        print(f"Chatting with {self.provider}/{self.model}: {len(messages)} messages")
        return {
            "role": "assistant",
            "content": f"Chat response for {len(messages)} messages",
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with the language model.

        Args:
            messages: List of messages in the conversation
            tools: List of tools to make available to the model
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum number of tokens to generate

        Returns:
            A dictionary containing the response and any tool calls
        """
        self.logger.debug(f"Creating chat completion with {len(messages)} messages")

        result = {"status": "complete", "content": "", "tool_calls": [], "error": None}

        try:
            # Prepare the request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
                self.logger.debug(f"Including {len(tools)} tools in the request")

            # Make the API call
            response = await self._call_chat_completion_api(params)

            # Extract the content and tool calls
            if response and hasattr(response, "choices") and len(response.choices) > 0:
                message = response.choices[0].message

                # Extract content
                result["content"] = message.content or ""

                # Extract tool calls if any
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        try:
                            # Parse the function arguments
                            arguments = json.loads(tool_call.function.arguments)

                            # Add to result
                            result["tool_calls"].append(
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": arguments,
                                    },
                                }
                            )
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse tool call arguments: {e}")
                            # Include the raw arguments
                            result["tool_calls"].append(
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments,
                                    },
                                }
                            )
            else:
                self.logger.warning("Received empty or invalid response from LLM")
                result["status"] = "error"
                result["error"] = "Empty or invalid response from LLM"

        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def _call_chat_completion_api(self, params: Dict[str, Any]) -> Any:
        """
        Call the chat completions API with the given parameters.

        Args:
            params: The parameters for the API call

        Returns:
            The API response
        """
        try:
            # For Ollama, we need to handle the API differently
            if self.provider == "ollama":
                # Check if we're using the correct endpoint
                if "/api" not in self.base_url:
                    # Use the direct Ollama API endpoint
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.base_url}/api/chat",
                            json={
                                "model": self.model,
                                "messages": params["messages"],
                                "options": {
                                    "temperature": params.get("temperature", 0.3),
                                },
                                "stream": False,
                            },
                        )

                        if response.status_code != 200:
                            self.logger.error(f"Ollama API error: {response.text}")
                            raise Exception(f"Ollama API error: {response.text}")

                        data = response.json()

                        # Convert to OpenAI-like format
                        return type(
                            "OllamaResponse",
                            (),
                            {
                                "choices": [
                                    type(
                                        "Choice",
                                        (),
                                        {
                                            "message": type(
                                                "Message",
                                                (),
                                                {
                                                    "content": data.get("message", {}).get("content", ""),
                                                    "tool_calls": [],  # Ollama doesn't support tool calls yet
                                                },
                                            )
                                        },
                                    )
                                ]
                            },
                        )
                else:
                    # Use the OpenAI-compatible endpoint
                    response = self._client.chat.completions.create(**params)
                    return response
            else:
                # For other providers, use the standard OpenAI client
                response = self._client.chat.completions.create(**params)
                return response
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise


def configure_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    Configure the global LLM client.

    Args:
        config: LLM configuration

    Returns:
        The configured LLM client
    """
    global _llm_client

    logger = logging.getLogger("fluent_mcp.llm_client")
    logger.info("Configuring LLM client")

    try:
        _llm_client = LLMClient(config)
        logger.info(f"LLM client configured successfully with provider {_llm_client.provider}")
        return _llm_client
    except LLMClientError as e:
        logger.error(f"Failed to configure LLM client: {str(e)}")
        raise


def get_llm_client() -> LLMClient:
    """
    Get the global LLM client.

    Returns:
        The configured LLM client

    Raises:
        LLMClientNotConfiguredError: If the client has not been configured
    """
    if _llm_client is None:
        error_msg = "LLM client has not been configured. Call configure_llm_client() first."
        logging.getLogger("fluent_mcp.llm_client").error(error_msg)
        raise LLMClientNotConfiguredError(error_msg)

    return _llm_client


async def run_embedded_reasoning(
    system_prompt: str, user_prompt: str, tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Run embedded reasoning with the language model.

    Args:
        system_prompt: The system prompt to provide context
        user_prompt: The user prompt to process
        tools: Optional list of tools to make available to the model

    Returns:
        A dictionary containing the response and any tool calls
    """
    logger = logging.getLogger("fluent_mcp.llm_client")
    logger.info("Running embedded reasoning")

    result = {
        "status": "error",
        "content": "",
        "tool_calls": [],
        "error": "LLM client not configured",
    }

    try:
        # Get the LLM client
        client = get_llm_client()

        # If tools is None, get all registered embedded tools
        if tools is None:
            from fluent_mcp.core.tool_registry import get_tools_as_openai_format

            tools = get_tools_as_openai_format()
            logger.info(f"Using {len(tools)} registered embedded tools")

        # Prepare the messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call chat completion
        result = await client.chat_completion(messages=messages, tools=tools, temperature=0.3, max_tokens=1000)

        logger.info("Embedded reasoning completed successfully")
        if result["tool_calls"]:
            logger.info(f"Model made {len(result['tool_calls'])} tool calls")

    except LLMClientNotConfiguredError as e:
        logger.error(f"LLM client not configured: {str(e)}")
        result["error"] = str(e)
    except Exception as e:
        logger.error(f"Error in embedded reasoning: {str(e)}")
        result["error"] = str(e)

    return result
