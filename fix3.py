import pathlib
f = pathlib.Path(r'D:\AI_kcMedicalResearch\src\modes\search.py')
lines = f.read_text(encoding='utf-8').splitlines(keepends=True)
# Fix 1: line 494 (0-indexed 493) – strip sub-mode digit prefix from joined query
# Replace:  query = ' '.join(direct_instructions)
# With:     query = ' '.join(direct_instructions).lstrip('0123456789. ').strip()
for i, line in enumerate(lines):
    if line == target:
        lines[i] = replacement
        print('Fix1 OK at line', i+1)
        break
else:
    print('Fix1 MISS – printing lines 492-496:')
    for i,l in enumerate(lines[491:496],start=492): print(i, repr(l))
f.write_text(''.join(lines), encoding='utf-8')
print('Saved search.py')
