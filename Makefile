.PHONY: help setup venv install run test clean mypy

# Default target
help:
	@echo "Available commands:"
	@echo "  setup    - Full project setup (Python + venv + deps)"
	@echo "  venv     - Create virtual environment only"
	@echo "  install  - Install dependencies"
	@echo "  run      - Start the server"
	@echo "  test     - Run tests"
	@echo "  mypy     - Run mypy type checks"
	@echo "  clean    - Clean up generated files"
	@echo "  help     - Show this help"

# Full setup
setup:
	@./setup.sh

# Create virtual environment
venv:
	@echo "🐍 Creating virtual environment..."
	python -m venv .venv
	@echo "✅ Virtual environment created!"
	@echo "To activate: source .venv/bin/activate"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Run the server
run:
	@echo "🎮 Starting Pocket Aces server..."
	.venv/bin/python main.py

# Run tests
test:
	@echo "🧪 Running tests..."
	.venv/bin/python -m pytest

# Type checking
mypy:
	@echo "🔎 Running mypy type checks..."
	.venv/bin/mypy .

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned up!"

# Development mode (auto-reload)
dev:
	@echo "🔄 Starting development server with auto-reload..."
	.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 