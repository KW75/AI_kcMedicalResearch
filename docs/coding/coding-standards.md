# Coding Standards

> Injected into Builder, Reviewer, and Tester prompts when --mode coding is active.

## Python Rules
- Use clear, descriptive names for variables and functions
- Keep functions small (under 50 lines) and single-purpose
- Add comments only to explain WHY, not WHAT
- Handle errors explicitly with try/except; never use bare except
- Do not hardcode secrets, API keys, passwords, or file paths
- Use environment variables for configuration
- Prefer standard library when possible; minimise dependencies
- Type hints on all function signatures
- Docstrings on all public functions

## HTML/CSS/JS Rules
- Valid HTML5 with proper DOCTYPE declaration
- Semantic elements (header, main, section, article, footer)
- CSS in a style block or separate file; no inline styles
- JavaScript at end of body or with defer attribute
- Accessible: alt text on images, aria labels on interactive elements
- Responsive: works on mobile and desktop viewports

## AI Agent Rules
- Make the smallest safe change that satisfies the requirement
- Explain every change and why it was made
- Do not edit unrelated files or add unrequested features
- Do not remove existing functionality unless explicitly asked
- Do not create hidden behaviour or side effects
- Do not remove safety checks, error handling, or validation

## Output Format Rules (CRITICAL)
- Return ONLY the complete code for ONE single file
- Do not include explanations or markdown prose outside code comments
- Do not generate multiple files or multiple code blocks
- Begin with the very first line of the file (e.g. <!DOCTYPE html> or import)
- End with the very last line (e.g. </html> or final closing brace)
- NEVER truncate, abbreviate, or summarise code
- NEVER use placeholders like "// ... rest of code" or "# TODO" or "[rest unchanged]"
- A response that ends mid-function or mid-file is a critical failure

## Testing Rules
- Add tests for all important logic paths
- Tests must be runnable with pytest
- Failed tests must be fixed before marking as PASS
- Aim for over 80% coverage on new code
