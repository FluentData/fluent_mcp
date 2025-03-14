#!/usr/bin/env python
"""
Run all tests for the fluent_mcp package.
"""

import logging
import os
import subprocess
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_all_tests")


def main():
    """Run all tests."""
    logger.info("Running all tests for fluent_mcp")

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Find all test files
    test_files = [
        f
        for f in os.listdir(script_dir)
        if f.startswith("test_") and f.endswith(".py") and f != os.path.basename(__file__)
    ]

    logger.info(f"Found {len(test_files)} test files: {', '.join(test_files)}")

    # Run each test file
    results = []
    for test_file in test_files:
        logger.info(f"Running {test_file}")
        result = subprocess.run(
            [sys.executable, os.path.join(script_dir, test_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"{test_file} passed")
            results.append(True)
        else:
            logger.error(f"{test_file} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            results.append(False)

    # Print summary
    logger.info(f"Tests completed: {sum(results)}/{len(results)} passed")

    # Return success if all tests passed
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
