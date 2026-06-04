with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if ('confidence' in line or 'iou' in line) and ('value=' in line):
            print(f"Line {i}: {line.strip()}")
