#!/usr/bin/env python
"""Analyze bracket template for tag matching issues"""

with open('templates/tournaments/bracket.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track opening and closing tags
for_stack = []
if_stack = []

for i, line in enumerate(lines, start=1):
    stripped = line.strip()
    
    # Track for loops
    if '{% for ' in stripped:
        for_stack.append((i, stripped))
        print(f"Line {i}: OPEN FOR - {stripped[:60]}")
    elif '{% endfor %}' in stripped:
        if for_stack:
            opened = for_stack.pop()
            print(f"Line {i}: CLOSE FOR (opened at {opened[0]})")
        else:
            print(f"Line {i}: ERROR - ENDFOR without matching FOR")
    
    # Track if statements
    if '{% if ' in stripped and '{% endif %}' not in stripped:
        if_stack.append((i, stripped))
        print(f"Line {i}: OPEN IF - {stripped[:60]}")
    elif '{% elif ' in stripped:
        print(f"Line {i}: ELIF - {stripped[:60]}")
    elif '{% else %}' in stripped:
        print(f"Line {i}: ELSE")
    elif '{% endif %}' in stripped:
        if if_stack:
            opened = if_stack.pop()
            print(f"Line {i}: CLOSE IF (opened at {opened[0]})")
        else:
            print(f"Line {i}: ERROR - ENDIF without matching IF")
    
    # Show lines 690-700 in detail
    if 690 <= i <= 700:
        print(f"  >>> Line {i}: {stripped}")

print("\n=== UNCLOSED TAGS ===")
if for_stack:
    print("Unclosed FOR loops:")
    for line_num, content in for_stack:
        print(f"  Line {line_num}: {content[:80]}")
if if_stack:
    print("Unclosed IF statements:")
    for line_num, content in if_stack:
        print(f"  Line {line_num}: {content[:80]}")

if not for_stack and not if_stack:
    print("All tags properly closed!")
