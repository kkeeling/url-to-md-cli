## Complete Github Issue

Perform these instructions to complete a Github issue.

### Instructions

1. Read the description of the issue to determine what needs to be done.
2. Create a new branch for the issue.
3. Think hard and determine if you need any documentation listed in the table of contents to complete the task. If you do, read the documentation.
4. Use the Aider AI Code Tool to implement the task you found in step 1 to completion
5. Use the Aider AI Code Tool to write unit tests for the task if applicable
6. Run your tests to ensure they pass. If they do not pass, fix the failures.
7. Run all tests in the project to ensure you have not broken any previous tests
8. Run the cli command `uv run kb_for_prompt/pages/kb_for_prompt.py` to run the application. If running the application fails or contains errors, fix the errors. Do not move on to the next instruction until the application runs without errors.
9. Perform a git commit with a message that summarizes the changes you made for the issue.
10. Use the github tool to create a pull request for the issue that mentions the issue title and number.
11. Mark the github issue as complete in the todo list

## Important Notes

- You are only complete when you have written unit tests for the task (if applicable) and all of those unit tests pass.
- You cannot create a pull request until you have written unit tests for the task (if applicable) and all of those unit tests pass.
- You must always follow the rules in `CLAUDE.md`
- If any documentation file is too large to read, use your grep tool to search the documentation files for relevant information.
