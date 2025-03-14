"""
Test script for the LLM client.
"""

import logging
import sys
import json
from fluent_mcp.core.llm_client import configure_llm_client, get_llm_client, LLMClientError, LLMClientNotConfiguredError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_llm_client")

def test_ollama_config():
    """Test Ollama configuration."""
    logger.info("Testing Ollama configuration")
    
    # Valid configuration
    valid_config = {
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama"  # Dummy value for Ollama
    }
    
    try:
        client = configure_llm_client(valid_config)
        logger.info("Ollama client configured successfully")
    except LLMClientError as e:
        logger.error(f"Failed to configure Ollama client: {str(e)}")
        return False
    
    # Invalid configuration (missing base_url)
    invalid_config = {
        "provider": "ollama",
        "model": "llama2",
        "api_key": "ollama"
    }
    
    try:
        client = configure_llm_client(invalid_config)
        logger.error("Ollama client configured with invalid config (should have failed)")
        return False
    except LLMClientError as e:
        logger.info(f"Correctly failed to configure Ollama client with invalid config: {str(e)}")
    
    return True

def test_groq_config():
    """Test Groq configuration."""
    logger.info("Testing Groq configuration")
    
    # Valid configuration
    valid_config = {
        "provider": "groq",
        "model": "llama2-70b-4096",
        "api_key": "gsk_1234567890"  # Fake API key
    }
    
    try:
        client = configure_llm_client(valid_config)
        logger.info("Groq client configured successfully")
    except LLMClientError as e:
        logger.error(f"Failed to configure Groq client: {str(e)}")
        return False
    
    # Invalid configuration (missing api_key)
    invalid_config = {
        "provider": "groq",
        "model": "llama2-70b-4096"
    }
    
    try:
        client = configure_llm_client(invalid_config)
        logger.error("Groq client configured with invalid config (should have failed)")
        return False
    except LLMClientError as e:
        logger.info(f"Correctly failed to configure Groq client with invalid config: {str(e)}")
    
    return True

def test_get_client():
    """Test getting the client."""
    logger.info("Testing get_llm_client")
    
    # Configure a client first
    config = {
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama"
    }
    
    try:
        configure_llm_client(config)
        client = get_llm_client()
        logger.info("Successfully got LLM client")
    except LLMClientError as e:
        logger.error(f"Failed to get LLM client: {str(e)}")
        return False
    
    return True

def test_unsupported_provider():
    """Test unsupported provider."""
    logger.info("Testing unsupported provider")
    
    config = {
        "provider": "unsupported",
        "model": "model",
        "api_key": "api_key"
    }
    
    try:
        client = configure_llm_client(config)
        logger.error("Configured client with unsupported provider (should have failed)")
        return False
    except LLMClientError as e:
        logger.info(f"Correctly failed to configure client with unsupported provider: {str(e)}")
    
    return True

def main():
    """Main entry point."""
    logger.info("Starting LLM client tests")
    
    # Run tests
    tests = [
        test_ollama_config,
        test_groq_config,
        test_get_client,
        test_unsupported_provider
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.exception(f"Error running test {test.__name__}: {str(e)}")
            results.append(False)
    
    # Print summary
    logger.info(f"Tests completed: {sum(results)}/{len(results)} passed")
    
    # Return success if all tests passed
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 