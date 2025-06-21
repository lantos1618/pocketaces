#!/usr/bin/env python3
"""
Setup script for Pocket Aces
Handles installation and initial setup
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def create_env_file():
    """Create .env file from template"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                content = f.read()
            with open(".env", "w") as f:
                f.write(content)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env with your API keys")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def create_directories():
    """Create necessary directories"""
    directories = [
        "static",
        "logs", 
        "voice_cache",
        "app/api/routes"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")

def create_init_files():
    """Create __init__.py files for Python packages"""
    init_files = [
        "app/__init__.py",
        "app/api/__init__.py", 
        "app/api/routes/__init__.py",
        "app/core/__init__.py",
        "app/core/game/__init__.py",
        "app/core/agents/__init__.py",
        "app/models/__init__.py",
        "app/store/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch(exist_ok=True)
    
    print("✅ Created __init__.py files")

def main():
    """Main setup function"""
    print("🎮 Setting up Pocket Aces...")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Create init files
    create_init_files()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env with your API keys")
    print("2. Run: python main.py")
    print("3. Visit: http://localhost:8000/docs")
    print("\nHappy coding! 🃏")

if __name__ == "__main__":
    main() 