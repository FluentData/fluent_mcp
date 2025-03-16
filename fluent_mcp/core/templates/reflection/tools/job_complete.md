---
name: job_complete
description: Guidance for using the job_complete tool to finalize tasks and return results
tools:
  - job_complete
---

# Using the job_complete Tool

The job_complete tool signals that a task is complete and returns the final result to the user. Use it when:
1. You have gathered all necessary information
2. You have synthesized the information into a coherent result
3. The task objectives have been met
4. No further tool calls are needed

## Current Context
Original Task: {{original_task}}
Current State: {{workflow_state}}

## Parameters

### result
The final result to return to the user. Format it clearly and comprehensively using markdown:

```markdown
# Task Result: [Title]

## Executive Summary
Brief (2-3 paragraphs) summary of key findings and conclusions.

## Detailed Analysis
### Section 1: [Topic]
Main points and supporting evidence...

### Section 2: [Topic]
Additional findings and analysis...

## Conclusions
* Key conclusion 1
* Key conclusion 2
* Key conclusion 3

## References and Sources
1. Source 1: Description
2. Source 2: Description
```

## Completion Checklist

Before using job_complete, verify:

### Information Completeness
- [ ] All required information has been gathered
- [ ] No critical questions remain unanswered
- [ ] Evidence supports all conclusions
- [ ] Sources are properly documented

### Result Quality
- [ ] Clear and logical structure
- [ ] Comprehensive coverage of the topic
- [ ] Well-supported conclusions
- [ ] Professional formatting

### Task Objectives
- [ ] Original task requirements met
- [ ] All specific questions answered
- [ ] Results are actionable
- [ ] Output matches expected format

### Technical Requirements
- [ ] Markdown formatting is correct
- [ ] All sections are properly structured
- [ ] Links and references are valid
- [ ] No placeholder text remains

## Best Practices

1. **Result Structure**
   - Use clear, descriptive headers
   - Organize information logically
   - Include all relevant details
   - Maintain consistent formatting

2. **Content Quality**
   - Be precise and specific
   - Support claims with evidence
   - Address all aspects of the task
   - Provide actionable insights

3. **Formatting**
   - Use markdown effectively
   - Create clear hierarchies
   - Make information scannable
   - Highlight key points

4. **Completeness**
   - Review all requirements
   - Check for missing information
   - Validate conclusions
   - Ensure proper references

## Common Pitfalls to Avoid

1. **Structure Issues**
   - Poor organization
   - Missing sections
   - Unclear hierarchy
   - Inconsistent formatting

2. **Content Problems**
   - Incomplete information
   - Unsupported claims
   - Missing context
   - Vague conclusions

3. **Technical Errors**
   - Invalid markdown
   - Broken links
   - Missing references
   - Formatting inconsistencies

4. **Task Alignment**
   - Not meeting requirements
   - Missing key objectives
   - Incomplete answers
   - Wrong format or style 