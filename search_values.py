import urllib.request
content = urllib.request.urlopen('http://localhost:5000').read().decode()
lines = content.split('\n')
for i, line in enumerate(lines):
    if ('confidence' in line or 'iou' in line) and ('value=' in line or 'step=' in line):
        print(f"Line {i}: {line.strip()}")
