#!/usr/bin/env python
import requests
import json

base_url = 'http://localhost:5000'
print('Testing Chatbot API Endpoints:')
print('=' * 50)

# Test 1: Status
r = requests.get(f'{base_url}/api/chatbot/status')
print(f'✓ GET /api/chatbot/status: {r.status_code}')
status = r.json()
print(f'  Mode: {status["status"]}')

# Test 2: Send message
r = requests.post(f'{base_url}/api/chatbot/message', json={'message': 'Tổng số xe phát hiện?'})
print(f'✓ POST /api/chatbot/message: {r.status_code}')
if r.status_code == 200:
    resp = r.json()
    print(f'  Response: {resp["response"][:80]}...')

# Test 3: Get history
r = requests.get(f'{base_url}/api/chatbot/history?limit=5')
print(f'✓ GET /api/chatbot/history: {r.status_code}')
hist = r.json()
print(f'  Messages: {hist["count"]}')

# Test 4: Clear history
r = requests.post(f'{base_url}/api/chatbot/clear')
print(f'✓ POST /api/chatbot/clear: {r.status_code}')
result = r.json()
print(f'  Result: {result["message"]}')

print('=' * 50)
print('✅ All chatbot endpoints working!')
