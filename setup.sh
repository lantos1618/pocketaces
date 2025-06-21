#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.12.3"
PROJECT_NAME="Pocket Aces"

echo -e "${BLUE}🚀 Setting up ${PROJECT_NAME}...${NC}"

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo -e "${RED}❌ pyenv not found!${NC}"
    echo -e "${YELLOW}Please install pyenv first:${NC}"
    echo "curl https://pyenv.run | bash"
    echo "Then restart your shell and run this script again."
    exit 1
fi

# Install Python version if not already installed
if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
    echo -e "${YELLOW}📦 Installing Python $PYTHON_VERSION...${NC}"
    pyenv install -s "$PYTHON_VERSION"
else
    echo -e "${GREEN}✅ Python $PYTHON_VERSION already installed${NC}"
fi

# Set local Python version
echo -e "${YELLOW}🔧 Setting local Python version...${NC}"
pyenv local "$PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"
    python -m venv .venv
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
for dir in static logs voice_cache app/api/routes; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✅ Created directory: $dir${NC}"
    fi

done

# Create __init__.py files for Python packages
for init_file in \
    app/__init__.py \
    app/api/__init__.py \
    app/api/routes/__init__.py \
    app/core/__init__.py \
    app/core/game/__init__.py \
    app/core/agents/__init__.py \
    app/models/__init__.py \
    app/store/__init__.py; do
    if [ ! -f "$init_file" ]; then
        touch "$init_file"
        echo -e "${GREEN}✅ Created $init_file${NC}"
    fi
done

# Create .env file from template if not present
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env with your API keys${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${BLUE}To activate your environment, run:${NC}"
echo -e "${YELLOW}source .venv/bin/activate${NC}"
echo -e "${BLUE}To start the server, run:${NC}"
echo -e "${YELLOW}python main.py${NC}" 