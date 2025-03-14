# Tests for Fluent MCP

This directory contains tests for the Fluent MCP package.

## Running Tests

You can run all tests using the `run_all_tests.py` script:

```bash
python tests/run_all_tests.py
```

Or run individual tests:

```bash
python tests/test_llm_client.py
python tests/test_server_run.py
python tests/test_interactive.py
```

## Test Files

- `test_llm_client.py`: Tests for the LLM client implementation
- `test_server_run.py`: Tests for the MCP server implementation
- `test_interactive.py`: Interactive tests for the MCP server with client-server communication
- `test_scaffolder.py`: Tests for the scaffolding functionality 