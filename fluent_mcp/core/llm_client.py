"""
LLM client implementation.

This module provides a client for interacting with language models
from various providers.
"""

import logging
import os
from typing import Dict, Any, Optional, Union, List

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
                error_msg = "Base URL is required for Ollama provider"
                self.logger.error(error_msg)
                raise LLMClientConfigError(error_msg)
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
                client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                self.logger.info(f"Initialized Ollama client with model {self.model}")
                return client
            elif self.provider == "groq":
                from openai import OpenAI
                client = OpenAI(
                    base_url="https://api.groq.com/openai/v1" if not self.base_url else self.base_url,
                    api_key=self.api_key
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
            "content": f"Chat response for {len(messages)} messages"
        }
