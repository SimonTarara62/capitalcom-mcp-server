#!/bin/bash
# Capital.com MCP Server - Installation Script

set -e  # Exit on error

echo "============================================"
echo "Capital.com MCP Server - Installation"
echo "============================================"
echo

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"
echo

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --quiet --upgrade pip
echo "✅ pip upgraded"
echo

# Install dependencies
echo "Installing dependencies..."
pip install --quiet -e ".[dev]"
echo "✅ Dependencies installed"
echo

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo
    echo "⚠️  IMPORTANT: Edit .env and add your Capital.com credentials:"
    echo "   - CAP_API_KEY"
    echo "   - CAP_IDENTIFIER"
    echo "   - CAP_API_PASSWORD"
    echo
else
    echo "⚠️  .env file already exists. Skipping..."
    echo
fi

# Verify installation
echo "Verifying installation..."
if python -c "import capital_mcp" 2>/dev/null; then
    echo "✅ Installation successful!"
else
    echo "❌ Installation verification failed"
    exit 1
fi
echo

echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "1. Edit .env file with your Capital.com credentials"
echo "2. Test the server: python -m capital_mcp.server"
echo "3. Configure your MCP client (Claude Desktop, Cursor, etc.)"
echo
echo "Virtual environment Python path:"
echo "  $(which python)"
echo
echo "Use this path in your MCP client configuration."
echo
echo "For detailed instructions, see:"
echo "  - README.md (integration guides)"
echo "  - USAGE.md (comprehensive usage guide)"
echo
