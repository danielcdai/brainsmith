import sys
from pathlib import Path

# Add the project root to sys.path, solve the import error
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))