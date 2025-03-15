# Rate Limiting in Fluent MCP

This guide explains how rate limiting works in Fluent MCP and how to configure it for your specific needs.

## Overview

Rate limiting is essential when working with LLM APIs to:

- Avoid hitting provider rate limits and getting blocked
- Manage costs by controlling request frequency
- Ensure fair resource distribution in multi-user environments
- Handle rate limit errors gracefully with automatic retries

Fluent MCP includes a robust rate limiting system with these key features:

- Provider-specific default rate limits
- Configurable limits and retry behavior
- Automatic detection of rate limit errors
- Exponential backoff retry mechanism
- Request tracking and history management

## Default Rate Limits

Fluent MCP comes with sensible default rate limits for different providers:

| Provider | Requests Per Minute | Requests Per Hour |
|----------|---------------------|-------------------|
| Ollama   | 60                  | 1000              |
| Groq     | 5                   | 100               |
| Others   | 10                  | 100               |

These defaults are conservative to ensure you don't hit API rate limits unexpectedly.

## Configuration

You can customize rate limiting behavior in your LLM client configuration:

```python
config = {
    "provider": "groq",
    "model": "llama-2-70b-4096",
    "api_key": "your_api_key",
    
    # Rate limiting configuration
    "rate_limits": {
        "requests_per_minute": 5,    # Maximum requests per minute
        "requests_per_hour": 100,    # Maximum requests per hour
    },
    
    # Retry configuration
    "retry_config": {
        "max_retries": 5,           # Maximum retry attempts
        "base_delay": 1.0,          # Starting delay in seconds
        "max_delay": 60.0           # Maximum delay in seconds
    }
}

# Configure the LLM client
from fluent_mcp.core.llm_client import configure_llm_client
llm_client = configure_llm_client(config)
```

## How It Works

### Request Tracking

The rate limiter tracks requests by:

1. Recording the timestamp of each request
2. Maintaining a history of recent requests
3. Cleaning up old requests from the history
4. Checking current request counts against the configured limits

### Rate Limit Checks

Before each request, the rate limiter:

1. Counts requests in the last minute and hour
2. Compares counts to the configured limits
3. Allows or denies the request based on these checks
4. Calculates retry timing if limits are exceeded

### Rate Limit Error Detection

The rate limiter detects rate limit errors by:

1. Examining exceptions thrown during API calls
2. Looking for common rate limit error patterns
3. Extracting retry information from response headers when available
4. Applying provider-specific detection logic

### Retry Logic

When rate limits are exceeded, the rate limiter:

1. Implements exponential backoff (each retry waits longer)
2. Respects "Retry-After" headers from the API when available
3. Retries up to the configured maximum number of attempts
4. Raises a LLMClientRateLimitError if all retries fail

## Error Handling

You can catch and handle rate limit errors in your code:

```python
from fluent_mcp.core.llm_client import run_embedded_reasoning, LLMClientRateLimitError

async def process_query(query):
    try:
        result = await run_embedded_reasoning(system_prompt, query)
        return result
    except LLMClientRateLimitError as e:
        retry_after = getattr(e, "retry_after", 60)
        print(f"Rate limit exceeded. Try again in {retry_after} seconds.")
        # Implement fallback strategy or schedule retry
```

## Provider-Specific Considerations

### Groq

Groq has strict rate limits, especially on the free tier:

- Free tier: ~5 requests per minute
- Retry-After headers are respected when provided
- Recommended to set conservative limits (3-5 RPM)

### Ollama

Ollama (self-hosted) has more flexible limits, but still benefits from rate limiting:

- Local instance: Limited by your hardware
- Consider limiting based on your server capabilities
- Default is 60 RPM, which works for most setups

## Best Practices

1. **Start Conservative**

   Begin with lower rate limits and gradually increase as needed.

2. **Monitor Usage**

   Log rate limit events to understand your usage patterns.

3. **Implement Caching**

   Cache responses for identical or similar requests to reduce API calls.

4. **Batch Requests**

   Combine multiple operations into a single request when possible.

5. **Handle Errors Gracefully**

   Provide a good user experience when rate limits are hit.

6. **Different Limits for Different Environments**

   Use different rate limits for development, testing, and production.

## Advanced Usage

### Custom Rate Limiter

For advanced scenarios, you can create a custom rate limiter:

```python
from fluent_mcp.core.llm_client import RateLimiter

# Create a custom rate limiter
rate_limiter = RateLimiter("groq", {
    "rate_limits": {
        "requests_per_minute": 10,
        "requests_per_hour": 200
    },
    "retry_config": {
        "max_retries": 8,
        "base_delay": 2.0,
        "max_delay": 120.0
    }
})

# Use the rate limiter directly
async def make_request():
    await rate_limiter.with_rate_limiting(my_api_function, arg1, arg2)
```

### Rate Limiting for Multiple Services

You can use different rate limiters for different services:

```python
# Create rate limiters for different services
groq_limiter = RateLimiter("groq", groq_config)
ollama_limiter = RateLimiter("ollama", ollama_config)

# Use the appropriate limiter based on the service
async def make_request(service, params):
    if service == "groq":
        return await groq_limiter.with_rate_limiting(api_call, params)
    elif service == "ollama":
        return await ollama_limiter.with_rate_limiting(api_call, params)
```

## Troubleshooting

If you're experiencing issues with rate limiting:

1. **Enable Debug Logging**

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Monitor Request History**

   Check the rate limiter's request history to understand usage patterns.

3. **Verify Rate Limit Error Detection**

   Ensure that rate limit errors are being correctly identified.

4. **Adjust Retry Configuration**

   Fine-tune retry parameters based on actual API behavior.

5. **Check for Other Errors**

   Some errors may be mistakenly identified as rate limit issues.

For more detailed troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).
