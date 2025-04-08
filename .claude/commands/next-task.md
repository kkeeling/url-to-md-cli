# Next Task

Find the next task in `$ARGUMENTS/todo.md`, read the prompt for the task from prompt file in `$ARGUMENTS` folder, and implement it to completion. You are only complete when you have written unit tests for the task and all of those unit tests pass. Upon completion, run all tests to ensure you have not broken any previous tests. If you have, fix them. Once you have done all of this, mark the task as complete in the todo list and move on to the next task.

## Instructions

1. Find the next task in `$ARGUMENTS/todo.md`
2. Read the prompt for the task from prompt file in `$ARGUMENTS` folder
3. Re-read the table of contents for the documentation:
   - `specs/docs/toc.md`
4. Think hard and determine if you need any documentation listed in the table of contents to complete the task. If you do, read the documentation.
5. Use the Aider AI Code Tool to implement the task you found in step 1 to completion
6. Use the Aider AI Code Tool to write unit tests for the task
7. Run all tests to ensure you have not broken any previous tests
8. Run the cli command `uv run kb_for_prompt/pages/kb_for_prompt.py` to run the application. If running the application fails or contains errors, fix the errors. Do not move on to the next instruction until the application runs without errors.
9. Mark the task as complete in the todo list

## Important Notes

- You are only complete when you have written unit tests for the task and all of those unit tests pass.
- You cannot mark your task as complete until you have written unit tests for the task and all of those unit tests pass.
- You cannot move on to the next task until you have marked the current task as complete.
- You must always follow the rules in `CLAUDE.md`
- If any documentation file is too large to read, use your grep tool to search the documentation files for relevant information.
