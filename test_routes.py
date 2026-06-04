#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
from app import app, traffic_bot

print("✓ traffic_bot imported:", type(traffic_bot))
print("\n✓ Chatbot routes registered:")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    if 'chatbot' in str(rule):
        print(f"  {rule}")

# Test that traffic_bot methods work
print("\n✓ traffic_bot methods:")
print(f"  - chat(): {callable(traffic_bot.chat)}")
print(f"  - get_status(): {callable(traffic_bot.get_status)}")
print(f"  - get_history(): {callable(traffic_bot.get_history)}")
print(f"  - clear_history(): {callable(traffic_bot.clear_history)}")

status = traffic_bot.get_status()
print(f"\n✓ Chatbot status: {status['status']}")
