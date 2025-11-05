#!/bin/bash
# Zimbra Migration Tool - Web UI Startup Script

echo "================================================"
echo "  Zimbra Migration Tool - Web UI"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if config.ini exists
if [ ! -f "config.ini" ]; then
    echo "Warning: config.ini not found"
    echo "Creating config.ini from config.ini.example..."
    if [ -f "config.ini.example" ]; then
        cp config.ini.example config.ini
        echo "Please edit config.ini with your server details before using the migration tool"
    else
        echo "Error: config.ini.example not found"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set port (default 5000, can be overridden with PORT environment variable)
PORT=${PORT:-5000}

echo ""
echo "================================================"
echo "  Starting Web UI on http://0.0.0.0:$PORT"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web application
python3 web_app.py

# Deactivate virtual environment on exit
deactivate
