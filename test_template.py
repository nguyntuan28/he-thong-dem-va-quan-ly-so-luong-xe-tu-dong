#!/usr/bin/env python3
import os

path = os.path.join(os.getcwd(), 'templates', 'dashboard.html')
print(f"Testing: {path}")

if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} bytes")
    print(f"Has CHATBOT: {'CHATBOT' in content}")
    print(f"Has FORCE RELOAD: {'FORCE RELOAD' in content}")
    
    # Find tabs section
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'class="tabs"' in line:
            print(f"\nTabs section (line {i}):")
            for j in range(i, min(i+8, len(lines))):
                print(f"  {j}: {lines[j][:120]}")
            break
else:
    print(f"File not found!")
