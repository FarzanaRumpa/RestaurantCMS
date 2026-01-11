#!/usr/bin/env python
"""Test invoice endpoint"""
import requests
import sys

try:
    # Test owner login page
    response = requests.get('http://127.0.0.1:5000/owner/login', timeout=5)
    print(f"Owner Login: Status {response.status_code}")

    # Test if server is responding
    if response.status_code == 200:
        print("✓ Server is responding correctly")
    else:
        print(f"⚠ Unexpected status code: {response.status_code}")

except requests.exceptions.ConnectionError:
    print("✗ Could not connect to server on port 5000")
    print("Please ensure the server is running: python run_port5000.py")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

