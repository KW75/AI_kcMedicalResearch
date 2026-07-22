# Coding Standards

# Coding Standards

> **Scope note:** This document applies to coding mode only.
> It is injected into AI prompts when --mode coding is active.
> It is not injected in writing, finance, or legal modes.


## Python Rules
- Use clear names for variables and functions.
- Keep functions small and readable.
- Add comments only when they help explain why something is done.
- Avoid unnecessary complexity.
- Handle errors clearly.
- Do not hardcode secrets, API keys, or passwords.
- Use environment variables for secrets.
- Prefer standard library tools when possible.

## AI Agent Rules
- Make small changes.
- Explain what changed.
- Do not edit unrelated files.
- Do not create hidden behavior.
- Do not remove safety checks.

## Testing Rules
- Add tests for important logic.
- Tests should be easy to run.
- Failed tests must be fixed before deployment.
