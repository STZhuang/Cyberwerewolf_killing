"""
Configure Python path to include the SDK package
"""
import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent.parent.parent
sdk_path = project_root / "packages" / "sdk-py"

# Add SDK path to Python path if not already present
if str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))