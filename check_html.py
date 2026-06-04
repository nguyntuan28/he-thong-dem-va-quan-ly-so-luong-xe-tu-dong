import urllib.request
content = urllib.request.urlopen('http://localhost:5000').read().decode()
for line in content.split('\n'):
    if 'id="confidence"' in line and 'value=' in line:
        print(line.strip())
        break
