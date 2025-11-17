#!/bin/bash

set -e

echo "🎙️  Voice Command macOS - Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Setup .env file
echo ""
echo "Setting up configuration..."
if [ ! -f "dotenv" ]; then
    cp dotenv.example dotenv 2>/dev/null || {
        echo "⚠️  .env file not created (dotenv.example not found)"
    }
fi

if [ -f "dotenv" ]; then
    # Check if API key is set
    if grep -q "your_deepgram_api_key_here" dotenv; then
        echo "⚠️  Please set your DEEPGRAM_API_KEY in dotenv file"
        echo ""
        echo "   nano dotenv"
        echo ""
    else
        echo "✓ Configuration file configured"
    fi
else
    echo "⚠️  dotenv file not found"
fi

# Test installation
echo ""
echo "Testing installation..."
python3 src/main.py check-permissions

echo ""
echo "✅  Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit dotenv and add your DEEPGRAM_API_KEY"
echo "  2. Run: python3 src/main.py run"
echo ""

