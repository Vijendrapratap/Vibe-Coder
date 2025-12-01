#!/bin/bash

echo "========================================="
echo "  VibeDoc Quick Start Script"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "========================================="
    echo "  IMPORTANT: Configure API Key"
    echo "========================================="
    echo ""
    echo "Please edit .env file and add your SiliconFlow API key:"
    echo "  nano .env"
    echo ""
    echo "Get your free API key at: https://siliconflow.cn"
    echo ""
    echo "After adding your API key, run:"
    echo "  python app.py"
    echo ""
else
    echo "✅ .env file found"
    echo ""
    echo "========================================="
    echo "  Starting VibeDoc..."
    echo "========================================="
    echo ""
    python app.py
fi
