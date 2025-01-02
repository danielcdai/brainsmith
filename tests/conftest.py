import sys
import os
from pathlib import Path


# Add the project root to sys.path, solve the import error
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
test_env_path = str(Path(__file__).parent / ".env")
if not os.path.exists(test_env_path):
    print("Environment file not found. Please run 'cp .env.example .env' to create it.")
    sys.exit(1)
os.environ["ENV_FILE_PATH"] = "tests/.env"