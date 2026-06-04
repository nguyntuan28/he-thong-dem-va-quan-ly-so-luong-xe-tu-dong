import os
os.chdir(r"c:\Users\nguyn\Downloads\files (1)")
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()
    # Find the confidence line
    idx = content.find('id="confidence"')
    if idx != -1:
        # Print surrounding context
        start = max(0, idx - 100)
        end = min(len(content), idx + 300)
        print(content[start:end])
