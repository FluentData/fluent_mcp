---
name: database_reflection
description: Tool-specific reflection template for database operations
application_mode: append
tools:
  - query_database
  - update_database
  - create_table
  - delete_table
---

# Database Operations Reflection

## Database-Specific Considerations
When working with database operations, consider:

1. Did you use the most efficient query structure?
2. Did you properly handle database connections and transactions?
3. Did you implement appropriate error handling for database operations?
4. Did you consider query performance and optimization?
5. Did you follow database security best practices?

## SQL Query Analysis
Review your SQL queries for:

1. Proper syntax and structure
2. Efficient joins and filtering
3. Appropriate use of indexes
4. Prevention of SQL injection vulnerabilities
5. Handling of NULL values and edge cases

## Database Performance Optimization
Consider these strategies for optimizing database operations:

1. Use prepared statements for repeated queries
2. Minimize the amount of data retrieved
3. Use appropriate indexing strategies
4. Consider query caching where appropriate
5. Batch operations when possible 