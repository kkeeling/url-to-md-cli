# Complete Feature

Follow these instructions to fully implement a feature.

## IMPORTANT CONTEXT

- The working folder for the feature spec, list of tasks, todo list, and individual task instructions is `$ARGUMENTS`
- Tasks are defined as the list of instructions in a prompt file, as listed in the todo list.

## Instructions

1. Read the spec file for the feature: named `spec.md` to understand the feature you are implementing
2. Read the todo list for the feature: named `todo.md` to understand the tasks you need to complete. You can refer to this todo list to see the tasks already completed and those that are still pending.
3. Starting with the first incomplete task in the todo list, complete every task in the todo list in the order they are listed. Never jump ahead or skip a task. For each task, follow the instructions in the next section.

## How to complete tasks in the todo list

1. Read the prompt for the task from prompt file
2. Re-read the table of contents for important documentation related to libraries and tools used in the project: `specs/docs/toc.md`
3. Think hard and determine if you need any documentation listed in the table of contents to complete the task. If you do, read the documentation files listed in the table of contents.
4. Use the Aider AI Code Tool to implement the task you found in step 1 to completion
5. Use the Aider AI Code Tool to write unit tests for the task
6. Run your unit tests to ensure they pass. If they do not pass, fix the failures.
7. Run all project unit tests to ensure you have not broken any previous tests. If you have fix the failures.
8. Run the cli command `uv run kb_for_prompt/pages/kb_for_prompt.py` to run the application. If running the application fails or contains errors, fix the errors. Do not move on to the next instruction until the application runs without errors.
8. Mark the task as complete in the todo list

## Important note about unit tests

- You must write unit tests for the task you are completing.
- When you are fixing failed tests, fix them one at a time. Do not fix all failures at once.
- When you are fixing failed tests, start by reading the source code that is causing the failure. Assume the issue is in the source code and not the unit tests. 

## Important Notes

- You are only complete when you have written unit tests for the task and all of those unit tests pass.
- You cannot mark your task as complete until you have written unit tests for the task and all of those unit tests pass.
- You cannot move on to the next task until you have marked the current task as complete.
- You must always follow the rules in `CLAUDE.md`
- If any documentation file is too large to read, use your grep tool to search the documentation files for relevant information.
- **Always** use the AI Code Tool to write code.
