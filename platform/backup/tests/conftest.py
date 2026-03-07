"""Test configuration for backup module."""

import sys
from pathlib import Path

# Add the backup directory to sys.path so we can import app.* directly
# without going through 'platform' (which conflicts with stdlib)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
