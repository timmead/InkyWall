#!/usr/bin/env python3
"""
Local setup script for InkyPi development

This script sets up the InkyPi project for local development without requiring
Raspberry Pi hardware. It creates necessary directories and files.
"""

import os
import sys
import subprocess

def setup_local_environment():
    """Setup the local development environment"""

    print("Setting up InkyPi for local development...")

    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create necessary directories relative to project root
    directories = [
        "src/static/images",
        "src/static/images/plugins",
        "src/static/images/saved",
        "src/static/images/local_outputs"
    ]

    for directory in directories:
        full_path = os.path.join(project_root, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create requirements file without hardware-specific dependencies
    local_requirements = """flask==3.1.1
python-dotenv==1.0.1
requests==2.32.3
urllib3==2.3.0
werkzeug==3.1.3
pillow==11.0.0
pytz==2025.2
openai==1.58.1
numpy==2.2.1"""

    with open("requirements-local.txt", "w") as f:
        f.write(local_requirements)

    print("Created requirements-local.txt")

    print("\nSetup complete! Next steps:")
    print("1. Install dependencies: pip install -r install/requirements-local.txt")
    print("2. Run the application: python src/inkypi_local.py")
    print("3. Open your browser to http://localhost:5000")
    print("4. Generated images will be saved in src/static/images/")

if __name__ == "__main__":
    setup_local_environment()
