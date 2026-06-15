# Product Requirements Document

## Project Name
AI Automation Tool

## Goal
Create a local Python tool with three AI roles:

1. Builder AI - creates or modifies code.
2. Reviewer AI - reviews the code and gives feedback.
3. Tester AI - suggests and later runs tests before deployment.

## Version 1 Scope
The first version will be simple and local.

It will:
- Read prompts from the ai/ folder.
- Read project documents from the docs/ folder.
- Allow the user to choose Builder, Reviewer, or Tester mode.
- Send the selected prompt and task to an AI model.
- Save AI responses into the reports/ folder.

## Not Included in Version 1
- No Docker yet.
- No web interface yet.
- No automatic deployment yet.
- No autonomous GitHub pull requests yet.
- No custom vector database/RAG yet.

## Success Criteria
Version 1 is successful when:
- The user can run the tool from the terminal.
- The user can choose one AI role.
- The AI returns a useful response.
- The response is saved in the correct report file.
