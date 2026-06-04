#!/bin/bash
# Vehicle Detection Web Server Startup Script (Linux/Mac)

echo ""
echo "================================================================================"
echo "  SmartPark - Vehicle Detection Web Interface"
echo "  YOLOv8-based Video Processing System"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    exit 1
fi

echo "[*] Python version:"
python3 --version

# Install requirements
echo ""
echo "[*] Installing/updating requirements..."
pip3 install --upgrade -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install requirements"
    exit 1
fi

echo ""
echo "================================================================================"
echo "[+] Starting Vehicle Detection Web Server..."
echo "================================================================================"
echo ""
echo "  Opening: http://localhost:5000"
echo "  Press Ctrl+C to stop the server"
echo ""

# Start Flask app
python3 app.py
