with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'id="confidence"' in line and i > 615 and i < 630:
            print(f"Line {i}: {line.strip()}")
