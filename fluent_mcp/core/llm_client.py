"""
LLM client implementation.

This module provides a client for interacting with language models
from various providers.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Global client instance
_llm_client = None


class RateLimiter:
    """
    Rate limiter for LLM API calls.

    Tracks request history and enforces rate limits with exponential backoff retry logic.
    """

    def __init__(self, provider: str, config: Dict[str, Any]):
        """
        Initialize the rate limiter.

        Args:
            provider: The LLM provider name
            config: Rate limiting configuration
        """
        self.provider = provider.lower()
        self.logger = logging.getLogger(f"fluent_mcp.rate_limiter.{self.provider}")

        # Default rate limits for different providers
        self.default_limits = {
            "ollama": {"requests_per_minute": 60, "requests_per_hour": 1000},
            "groq": {"requests_per_minute": 5, "requests_per_hour": 100},
            # Add other providers as needed
        }

        # Get provider-specific defaults or use conservative defaults
        provider_defaults = self.default_limits.get(provider, {"requests_per_minute": 10, "requests_per_hour": 100})

        # Set rate limits from config or use defaults
        rate_limit_config = config.get("rate_limits", {})
        self.requests_per_minute = rate_limit_config.get(
            "requests_per_minute", provider_defaults["requests_per_minute"]
        )
        self.requests_per_hour = rate_limit_config.get("requests_per_hour", provider_defaults["requests_per_hour"])

        # Retry configuration
        retry_config = config.get("retry_config", {})
        self.max_retries = retry_config.get("max_retries", 5)
        self.base_delay = retry_config.get("base_delay", 1.0)  # Base delay in seconds
        self.max_delay = retry_config.get("max_delay", 60.0)  # Maximum delay in seconds

        # Request history tracking
        self.request_history: List[datetime] = []

        self.logger.info(
            f"Rate limiter configured for {provider}: "
            f"{self.requests_per_minute} requests/minute, "
            f"{self.requests_per_hour} requests/hour, "
            f"max {self.max_retries} retries"
        )

    def _clean_history(self):
        """
        Clean up old requests from history.
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Keep only requests from the last hour
        self.request_history = [dt for dt in self.request_history if dt > one_hour_ago]

    async def check_rate_limit(self) -> Tuple[bool, Optional[float]]:
        """
        Check if we're within rate limits.

        Returns:
            A tuple of (is_allowed, retry_after)
        """
        self._clean_history()
        now = datetime.now()

        # Check hour limit
        requests_last_hour = len(self.request_history)
        if requests_last_hour >= self.requests_per_hour:
            oldest = min(self.request_history)
            retry_after = (oldest + timedelta(hours=1) - now).total_seconds()
            self.logger.warning(
                f"Hour rate limit reached: {requests_last_hour}/{self.requests_per_hour} requests. "
                f"Try again in {retry_after:.1f} seconds."
            )
            return False, max(0, retry_after)

        # Check minute limit
        one_minute_ago = now - timedelta(minutes=1)
        requests_last_minute = sum(1 for dt in self.request_history if dt > one_minute_ago)

        if requests_last_minute >= self.requests_per_minute:
            # Find the oldest request within the last minute
            minute_requests = [dt for dt in self.request_history if dt > one_minute_ago]
            oldest_minute = min(minute_requests)
            retry_after = (oldest_minute + timedelta(minutes=1) - now).total_seconds()
            self.logger.warning(
                f"Minute rate limit reached: {requests_last_minute}/{self.requests_per_minute} requests. "
                f"Try again in {retry_after:.1f} seconds."
            )
            return False, max(0, retry_after)

        return True, None

    def record_request(self):
        """
        Record a new request in the history.
        """
        self.request_history.append(datetime.now())

    def detect_rate_limit_error(self, exception: Exception) -> Optional[float]:
        """
        Detect if an exception is due to rate limiting and extract retry information.

        Args:
            exception: The exception to check

        Returns:
            Retry after seconds if it's a rate limit error, None otherwise
        """
        error_text = str(exception).lower()

        # Provider-specific rate limit detection
        if self.provider == "groq":
            # Groq rate limit detection logic
            if "rate limit" in error_text or "too many requests" in error_text or "429" in error_text:
                # Try to extract retry-after header if available in the exception
                retry_after = None

                # Check if it's an OpenAI error with headers
                if hasattr(exception, "headers") and getattr(exception, "headers") is not None:
                    retry_after_str = exception.headers.get("retry-after")
                    if retry_after_str:
                        try:
                            retry_after = float(retry_after_str)
                        except (ValueError, TypeError):
                            pass

                # If we couldn't extract retry-after, use exponential backoff
                if retry_after is None:
                    retry_after = 60.0  # Default for Groq

                return retry_after

        elif self.provider == "ollama":
            # Ollama rate limit detection logic
            if "rate limit" in error_text or "too many requests" in error_text:
                return 5.0  # Default for Ollama

        # Generic rate limit detection as a fallback
        if any(phrase in error_text for phrase in ["rate limit", "too many requests", "429", "throttl"]):
            return 10.0  # Generic default

        return None

    async def with_rate_limiting(self, func, *args, **kwargs):
        """
        Execute a function with rate limiting and retry logic.

        Args:
            func: The function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function

        Raises:
            LLMClientRateLimitError: If rate limits are exceeded after all retries
            Any other exceptions raised by the function
        """
        retries = 0

        while True:
            # Check if we're within rate limits
            is_allowed, retry_after = await self.check_rate_limit()

            if not is_allowed:
                if retries >= self.max_retries:
                    raise LLMClientRateLimitError(
                        f"Rate limit exceeded after {retries} retries. Try again later.", retry_after=retry_after
                    )

                # Wait and retry
                wait_time = retry_after if retry_after is not None else self.base_delay * (2**retries)
                wait_time = min(wait_time, self.max_delay)

                self.logger.info(
                    f"Rate limit exceeded. Retrying in {wait_time:.1f} seconds (retry {retries+1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                retries += 1
                continue

            # Record this request
            self.record_request()

            try:
                # Execute the function
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if this is a rate limit error
                retry_after = self.detect_rate_limit_error(e)

                if retry_after is not None:
                    if retries >= self.max_retries:
                        raise LLMClientRateLimitError(
                            f"Rate limit error after {retries} retries: {str(e)}", retry_after=retry_after
                        )

                    # Wait and retry
                    wait_time = retry_after
                    self.logger.info(
                        f"Rate limit error detected. Retrying in {wait_time:.1f} seconds (retry {retries+1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    retries += 1
                else:
                    # Not a rate limit error, re-raise
                    raise


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMClientConfigError(LLMClientError):
    """Exception raised for configuration errors."""

    pass


class LLMClientNotConfiguredError(LLMClientError):
    """Exception raised when the client is not configured."""

    pass


class LLMClientRateLimitError(LLMClientError):
    """Exception raised when rate limits are hit."""

    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


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

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(self.provider, config)

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

        try:
            # Make the API call with rate limiting
            response = await self.rate_limiter.with_rate_limiting(self._call_chat_completion_api, params)

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

        except LLMClientRateLimitError as e:
            self.logger.error(f"Rate limit error: {str(e)}")
            result["status"] = "error"
            result["error"] = f"Rate limit exceeded: {str(e)}"
            if e.retry_after:
                result["retry_after"] = e.retry_after
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
    system_prompt: str,
    user_prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    prompt: Optional[Dict[str, Any]] = None,
    project_id: Optional[str] = None,
    enable_reflection: bool = False,
    max_reflection_iterations: int = 3,
) -> Dict[str, Any]:
    """
    Run embedded reasoning with the language model.

    Args:
        system_prompt: The system prompt to provide context
        user_prompt: The user prompt to process
        tools: Optional list of tools to make available to the model
        prompt: Optional prompt dictionary from the prompt loader
        project_id: Optional project ID for budget tracking (defaults to server name)
        enable_reflection: Whether to enable the reflection loop
        max_reflection_iterations: Maximum number of reflection iterations

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
        if not client:
            raise LLMClientNotConfiguredError("LLM client not configured")

        # Get the server instance if available
        from fluent_mcp.core.server import get_server

        server = get_server()

        # Generate a prompt ID for tracking
        prompt_id = str(uuid.uuid4())

        # Get tools from the prompt if available
        if prompt and not tools:
            from fluent_mcp.core.prompt_loader import get_prompt_tools

            tools = get_prompt_tools(prompt)

        # Run the LLM with the prompt and tools
        logger.info("Calling LLM with embedded reasoning prompt")
        response = await client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=tools,
        )

        # Process the response
        result = {
            "status": "complete",
            "content": response.get("content", ""),
            "tool_calls": response.get("tool_calls", []),
        }

        # If reflection is enabled and there are tool calls, run the reflection loop
        if enable_reflection and result["tool_calls"]:
            logger.info("Enabling reflection loop for embedded reasoning")

            # Import the reflection loop
            from fluent_mcp.core.reflection import ReflectionLoop

            # Create a reflection loop instance
            reflection_loop = ReflectionLoop()

            # Execute tool calls to get results for reflection
            tool_results = []

            if server and server.budget_manager and project_id:
                from fluent_mcp.core.tool_execution import execute_embedded_tool

                for tool_call in result["tool_calls"]:
                    if tool_call["type"] == "function":
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]

                        # Execute the tool with budget enforcement
                        tool_result = await execute_embedded_tool(function_name, arguments, project_id, prompt_id)

                        # Add the result to the list
                        tool_results.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "function_name": function_name,
                                "arguments": arguments,
                                "result": tool_result,
                            }
                        )

            # Run the reflection loop
            reflection_result = await reflection_loop.run_reflection(
                previous_reasoning=result["content"],
                tool_calls=result["tool_calls"],
                tool_results=tool_results,
                llm_client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_iterations=max_reflection_iterations,
            )

            # Update the result with the reflection result
            result["content"] = reflection_result["content"]
            result["tool_calls"] = reflection_result["tool_calls"]
            result["reflection_history"] = reflection_result["reflection_history"]
            result["reflection_iterations"] = reflection_result["iterations"]

            # Add tool results if available
            if "tool_results" in reflection_result:
                result["tool_results"] = reflection_result["tool_results"]

        # If no reflection or reflection is disabled, process tool calls normally
        elif result["tool_calls"]:
            logger.info(f"Model made {len(result['tool_calls'])} tool calls")

            # Execute tool calls with budget enforcement if budget manager is available
            if server and server.budget_manager and project_id:
                from fluent_mcp.core.tool_execution import execute_embedded_tool

                # Add tool results to the response
                result["tool_results"] = []

                for tool_call in result["tool_calls"]:
                    if tool_call["type"] == "function":
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]

                        # Execute the tool with budget enforcement
                        tool_result = await execute_embedded_tool(function_name, arguments, project_id, prompt_id)

                        # Add the result to the response
                        result["tool_results"].append(
                            {
                                "tool_call_id": tool_call["id"],
                                "function_name": function_name,
                                "arguments": arguments,
                                "result": tool_result,
                            }
                        )

    except LLMClientNotConfiguredError as e:
        logger.error(f"LLM client not configured: {str(e)}")
        result["error"] = str(e)
    except Exception as e:
        logger.error(f"Error in embedded reasoning: {str(e)}")
        result["error"] = str(e)

    return result
