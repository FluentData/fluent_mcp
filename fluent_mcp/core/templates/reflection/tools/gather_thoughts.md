---
name: gather_thoughts
description: Guidance for using the gather_thoughts tool to organize thinking and maintain workflow state
tools:
  - gather_thoughts
---

# Using the gather_thoughts Tool

The gather_thoughts tool helps you organize your thinking across iterations and maintain workflow state. Use it to:
1. Analyze the results of tool calls
2. Plan your next steps
3. Accumulate information in a structured format
4. Signal when a task is complete

## Current Context
Original Task: {{original_task}}
Remaining Budget: {{remaining_budget}} iterations

## Parameters

### analysis
Your analysis of the current situation and tool results. Include:
- What you learned from the last tool execution
- How this information relates to previous knowledge
- Any patterns or insights you've identified
- Potential gaps in understanding

### next_steps
Your plan for what to do next. Be specific about:
- Which tool to use next and why
- What information you need to gather
- How this advances the task
- Contingency plans if needed

### workflow_state
The accumulated information and state in markdown format. Structure it as:

```markdown
# Task Progress

## Key Findings
- Important discovery 1
- Important discovery 2

## Open Questions
1. Question to investigate
2. Area to explore

## Evidence and Sources
* Source 1: Key points
* Source 2: Relevant information

## Current Status
Summary of where we are in the process
```

### is_complete
Boolean flag indicating whether the task is ready for completion. Set to true when:
- All necessary information has been gathered
- The task objectives have been met
- The results are well-organized and complete
- No further investigation is needed

## Best Practices

1. **State Management**
   - Keep the workflow_state organized and clear
   - Update incrementally with new information
   - Maintain a clear structure with headers
   - Link related information together

2. **Analysis Quality**
   - Be specific and detailed
   - Connect new information to existing knowledge
   - Identify patterns and relationships
   - Note both certainties and uncertainties

3. **Planning**
   - Consider the remaining budget
   - Prioritize critical information gaps
   - Have clear objectives for each step
   - Be ready to adapt the plan

4. **Completion Criteria**
   - Only mark complete when truly finished
   - Ensure all objectives are met
   - Verify information is well-organized
   - Check that conclusions are supported

## Common Pitfalls to Avoid

1. **Workflow State**
   - Disorganized or flat structure
   - Missing important details
   - Redundant information
   - Poor formatting

2. **Analysis**
   - Too vague or general
   - Missing key connections
   - Overlooking important details
   - Jumping to conclusions

3. **Planning**
   - Unfocused next steps
   - Ignoring budget constraints
   - Lack of clear objectives
   - Not adapting to new information

4. **Task Completion**
   - Premature completion
   - Incomplete information
   - Poor organization
   - Missing conclusions 