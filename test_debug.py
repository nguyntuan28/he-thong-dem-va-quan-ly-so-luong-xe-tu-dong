import urllib.request
response = urllib.request.urlopen('http://localhost:5000/debug/template').read().decode()
print(response)
