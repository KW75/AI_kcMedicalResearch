import pathlib

file = pathlib.Path('src/modes/coding.py')
src = file.read_text(encoding='utf-8')

old = (
    '        parts.append(\n'
    '            "## Task\\n"\n'
    '            "Build a complete, well-structured application based on the direct task "\n'
    '            "instructions above and the background guidelines in the system prompt.\\n"\n'
    '            "Each instruction represents a feature, function, or component of ONE "\n'
    '            "single application. Produce the COMPLETE application as a single coherent "\n'
    '            "file. Use the most appropriate language and file format for the task "\n'
    '            "described in the instructions above.\\n"\n'
    '            "IMPORTANT: Write the ENTIRE file from first line to last. "\n'
    '            "Do NOT stop early. Do NOT use placeholders. "\n'
    '            "The output must be a complete, immediately runnable file. "\n'
    '            "For HTML files, the last line must be </html>. "\n'
    '            "For Python files, the last line must close all functions and classes. "\n'
    '            "If you are running out of space, prioritise completing the logic over adding comments."\n'
    '        )'
)

new = (
    '        parts.append(\n'
    '            "## Task\\n"\n'
    '            "Build a complete, immediately runnable application implementing EVERY "\n'
    '            "feature listed in the Direct Task Instructions above.\\n"\n'
    '            "STRICT RULES:\\n"\n'
    '            "1. Every button, input, and display element mentioned in the instructions "\n'
    '            "   MUST exist as an HTML element with a matching id.\\n"\n'
    '            "2. Every HTML element id referenced in JavaScript MUST exist in the HTML "\n'
    '            "   DOM. Never reference an id that is not in the HTML.\\n"\n'
    '            "3. All button click handlers MUST be wired with addEventListener in the "\n'
    '            "   init() function called on DOMContentLoaded.\\n"\n'
    '            "4. Use the EXACT feature names from the instructions for button labels "\n'
    '            "   and element ids (e.g. start-btn, stop-btn, beep-period).\\n"\n'
    '            "5. Do NOT invent features not listed in the instructions.\\n"\n'
    '            "6. Do NOT generate a generic template - implement the specific "\n'
    '            "   application described.\\n"\n'
    '            "7. Write the ENTIRE file from first line to last line.\\n"\n'
    '            "8. Do NOT stop early, do NOT use placeholders.\\n"\n'
    '            "9. For HTML: last line must be </html>.\\n"\n'
    '            "10. For Python: last line must close all functions and classes.\\n"\n'
    '            "If running out of space, prioritise completing logic over comments."\n'
    '        )'
)

if old in src:
    src = src.replace(old, new, 1)
    file.write_text(src, encoding='utf-8')
    print('Replaced OK')
else:
    print('ERROR: old block not found')
