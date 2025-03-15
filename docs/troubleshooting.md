# Troubleshooting Guide for Fluent MCP

This guide provides solutions for common issues you might encounter when using Fluent MCP.

## Rate Limiting Issues

### Symptoms

- Error messages containing "rate limit exceeded" or "too many requests"
- LLMClientRateLimitError exceptions
- Requests failing with HTTP 429 status code
- Slow or failed responses from the LLM API

### Solutions

1. **Configure Rate Limits**

   Set appropriate rate limits in your configuration:

   ```python
   config = {
       "provider": "groq",
       "model": "llama-2-70b-4096",
       "api_key": "your_api_key",
       "rate_limits": {
           "requests_per_minute": 5,   # Adjust based on your API tier
           "requests_per_hour": 100    # Adjust based on your API tier
       }
   }
   ```

2. **Handle Rate Limit Errors**

   Catch and handle rate limit errors in your code:

   ```python
   from fluent_mcp.core.llm_client import LLMClientRateLimitError
   
   try:
       result = await run_embedded_reasoning(system_prompt, user_prompt)
   except LLMClientRateLimitError as e:
       retry_after = getattr(e, "retry_after", 60)
       print(f"Rate limit exceeded. Try again in {retry_after} seconds.")
       # Maybe schedule a retry or use a fallback
   ```

3. **Upgrade Your API Tier**

   If you're consistently hitting rate limits, consider upgrading your API tier with your provider.

4. **Implement Request Batching**

   Batch multiple requests together to reduce API calls:

   ```python
   # Instead of making 10 separate calls
   batch_prompts = [prompt1, prompt2, prompt3, ...]
   batch_results = await process_batch(batch_prompts)
   ```

5. **Use Caching**

   Implement caching for common requests:

   ```python
   import functools

   @functools.lru_cache(maxsize=100)
   async def cached_reasoning(system_prompt, user_prompt):
       return await run_embedded_reasoning(system_prompt, user_prompt)
   ```

## LLM Client Connection Issues

### Symptoms

- Error messages containing "connection refused" or "connection error"
- Timeouts when connecting to LLM providers
- LLMClientConfigError exceptions

### Solutions

1. **Check API Key**

   Ensure your API key is valid and has not expired.

2. **Verify Base URL**

   Make sure the base URL for your provider is correct:

   - Ollama: Usually "http://localhost:11434" (for local deployment)
   - Groq: "https://api.groq.com/openai/v1"

3. **Check Network Connection**

   Ensure your network allows connections to the API endpoint.

4. **Increase Timeout**

   For slow connections, increase the timeout:

   ```python
   import httpx
   
   # Use a custom client with longer timeout
   async with httpx.AsyncClient(timeout=60.0) as client:
       # Custom request logic
   ```

5. **Verify Provider Availability**

   Check if the provider's service is currently operational.

## Tool Registration Issues

### Symptoms

- Tools not appearing in available tools list
- "Tool not found" errors
- Functions not being correctly recognized as tools

### Solutions

1. **Check Decorator Usage**

   Ensure you're using the correct decorator:

   ```python
   from fluent_mcp.core.tool_registry import register_embedded_tool
   
   @register_embedded_tool()  # Note the parentheses
   def my_tool():
       pass
   ```

2. **Import Tools Properly**

   Make sure tools are imported before server creation:

   ```python
   from my_package.tools import my_tool, another_tool
   
   server = create_mcp_server(
       server_name="my_server",
       embedded_tools=[my_tool, another_tool],
       # ...
   )
   ```

3. **Check Tool Signatures**

   Ensure your tool functions have proper type annotations:

   ```python
   @register_embedded_tool()
   def my_tool(param1: str, param2: int = 42) -> Dict[str, Any]:
       """
       Tool description.
       
       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2
           
       Returns:
           Dictionary with results
       """
       # Tool implementation
   ```

4. **Tool Discovery**

   If your tools aren't being discovered automatically, try registering them explicitly:

   ```python
   from fluent_mcp.core.tool_registry import register_tool
   
   register_tool(my_tool)
   ```

## Embedded Reasoning Issues

### Symptoms

- LLM not using tools
- Tool calls failing
- Empty or unexpected responses

### Solutions

1. **Provide Clear System Prompts**

   Make sure your system prompt explicitly instructs the LLM to use tools:

   ```python
   system_prompt = """You are a helpful assistant with access to tools.
   When the user asks you a question requiring calculation or data lookup,
   use the appropriate tool to help answer their question.
   ALWAYS use tools when they would be helpful."""
   ```

2. **Check Tool Descriptions**

   Ensure your tools have clear, detailed docstrings that explain what they do.

3. **Tool Context Limit**

   If you have many tools, prioritize the most relevant ones:

   ```python
   # Select only the tools needed for this specific task
   math_tools = [calculate_sum, calculate_average, calculate_product]
   result = await run_embedded_reasoning(system_prompt, user_prompt, tools=math_tools)
   ```

4. **Debug Tool Calls**

   Add logging to see what tool calls are being made:

   ```python
   for tool_call in result["tool_calls"]:
       if tool_call["type"] == "function":
           function_name = tool_call["function"]["name"]
           arguments = tool_call["function"]["arguments"]
           print(f"Tool called: {function_name}")
           print(f"Arguments: {json.dumps(arguments, indent=2)}")
   ```

5. **Verify Model Capabilities**

   Make sure your chosen model supports function calling or tool use.

## Server Startup Issues

### Symptoms

- Error messages when starting the server
- Server fails to initialize
- Configuration errors

### Solutions

1. **Check Environment Variables**

   Make sure all required environment variables are set:

   ```bash
   export FLUENT_LLM_PROVIDER=ollama
   export FLUENT_LLM_MODEL=llama2
   export FLUENT_LLM_BASE_URL=http://localhost:11434
   export FLUENT_LLM_API_KEY=your_api_key_here
   ```

2. **Validate Config File**

   Ensure your configuration file has the correct format and required fields.

3. **Check Port Availability**

   Make sure the port you're trying to use isn't already in use by another application.

4. **Run in Debug Mode**

   Enable debug mode for more detailed logging:

   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

5. **Check Dependencies**

   Ensure all dependencies are correctly installed:

   ```bash
   pip install -r requirements.txt
   # or
   pip install fluent_mcp[all]
   ```

## Prompt Loading Issues

### Symptoms

- Prompts not loading
- InvalidFrontmatterError or MissingRequiredFieldError exceptions
- Prompt format errors

### Solutions

1. **Check Prompt Format**

   Ensure your prompt files have the correct format:

   ```markdown
   ---
   name: My Prompt
   description: A description of what this prompt does
   ---
   
   Your actual prompt text here...
   ```

2. **Check Prompts Directory**

   Make sure you're pointing to the correct prompts directory:

   ```python
   server = create_mcp_server(
       server_name="my_server",
       prompts_dir="./my_project/prompts",  # Use absolute or relative path
       # ...
   )
   ```

3. **Validate YAML Frontmatter**

   Check that your YAML frontmatter is valid:
   - No tabs (use spaces for indentation)
   - No missing colons after keys
   - No invalid characters

4. **Required Fields**

   Ensure all required fields are present in the frontmatter:
   - `name`
   - `description`

5. **Manual Prompt Loading**

   Try loading prompts manually to debug issues:

   ```python
   from fluent_mcp.core.prompt_loader import parse_markdown_with_frontmatter
   
   try:
       prompt = parse_markdown_with_frontmatter("path/to/prompt.md")
       print(f"Loaded prompt: {prompt['config']['name']}")
   except Exception as e:
       print(f"Error loading prompt: {e}")
   ```

## Performance Issues

### Symptoms

- Slow response times
- High memory usage
- Timeouts or request failures

### Solutions

1. **Use Async Methods Properly**

   Make sure you're using async/await correctly:

   ```python
   # Correct usage
   async def process_requests():
       result = await run_embedded_reasoning(system_prompt, user_prompt)
       return result
   
   # Run the async function
   import asyncio
   asyncio.run(process_requests())
   ```

2. **Implement Caching**

   Cache responses for frequent queries:

   ```python
   import functools
   
   @functools.lru_cache(maxsize=100)
   def get_cached_result(prompt_hash):
       # Return cached result
   ```

3. **Optimize Tool Execution**

   Make your tools efficient and avoid unnecessary computation.

4. **Use Connection Pooling**

   Reuse HTTP connections when making multiple requests:

   ```python
   async with httpx.AsyncClient() as client:
       # Make multiple requests with the same client
   ```

5. **Monitor and Profile**

   Use profiling tools to identify bottlenecks:

   ```python
   import cProfile
   
   cProfile.run('my_function()')
   ```

## Getting Additional Help

If you're still experiencing issues after trying the solutions in this guide:

1. **Check the GitHub Issues**

   Search existing issues to see if others have encountered the same problem.

2. **Create a New Issue**

   If you can't find a solution, create a new issue with:
   - A clear description of the problem
   - Steps to reproduce
   - Expected vs. actual behavior
   - Error messages and logs
   - Your environment details (OS, Python version, etc.)

3. **Join the Community**

   Participate in the community discussions to get help from other users.

4. **Check for Updates**

   Make sure you're using the latest version of Fluent MCP, as many issues are fixed in newer releases.
