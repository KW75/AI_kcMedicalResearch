# Coding Standards

## General Rules
- Write clean, readable, self-documenting code.
- Use clear descriptive names for variables, functions, and classes.
- Keep functions small — one function, one responsibility.
- Add comments only to explain WHY, not WHAT.
- Handle all errors explicitly — never silently swallow exceptions.
- Do not hardcode secrets, API keys, or passwords. Use environment variables.
- Prefer standard library tools over third-party dependencies where practical.

## HTML / CSS / JavaScript Rules
- Always include <!DOCTYPE html> as the very first line of HTML files.
- Use semantic HTML5 elements (header, main, section, article, footer).
- Keep CSS in a <style> block or separate .css file — not inline styles.
- Use const and let — never var.
- Handle all button click events with addEventListener, not onclick attributes.
- Validate all user inputs before processing.

## Python Rules
- Follow PEP 8 style conventions.
- Use type hints on all function signatures.
- Use dataclasses or named tuples for structured data.
- Never use bare except: — always catch specific exception types.
- Use pathlib.Path for all file system operations.

## SQL Rules
- Use parameterised queries — never string concatenation for SQL.
- Include CREATE TABLE IF NOT EXISTS rather than CREATE TABLE.
- Add appropriate indexes on foreign keys and frequently queried columns.

## Output Quality
- The code must be complete and runnable as delivered.
- Do not include placeholder comments like # TODO or # implement this.
- Do not truncate the output — always deliver the full file.
