# Architecture Guidelines

## General Principles
- Build the simplest architecture that satisfies the requirements.
- Separate concerns — keep data, logic, and presentation in distinct layers.
- Write code that is easy to read, easy to test, and easy to extend.
- Avoid premature optimisation — make it work first, then make it fast.

## HTML Application Architecture
- Keep all HTML structure in the HTML file.
- Keep all styling in a <style> block or separate CSS file.
- Keep all behaviour in a <script> block or separate JS file.
- Use data attributes to connect HTML elements to JavaScript behaviour.
- Store application state in plain JavaScript objects — not in the DOM.

## Python Application Architecture
- Entry point: main() function called from if __name__ == "__main__".
- Configuration: read from environment variables or a config file, never hardcoded.
- I/O: separate file reading/writing from business logic.
- Error handling: catch exceptions at the boundary of the application, not deep inside.

## File Organisation
- One file per logical component where practical.
- Name files after what they do, not what they are (timer.html not page1.html).
- Keep related files in the same folder.
