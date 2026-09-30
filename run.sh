#!/bin/bash

# VK LEDGUR CONVERTER - Run Script for Mac/Linux

echo ""
echo "========================================="
echo "VK LEDGUR CONVERTER - Flask Application"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please download Python from https://www.python.org/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the Flask app
echo ""
echo "========================================="
echo "Starting VK LEDGUR CONVERTER..."
echo "========================================="
echo ""
echo "Visit: http://localhost:5000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python3 app.py
