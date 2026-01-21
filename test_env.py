from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

print(f"ENABLE_EXTERNAL_VERIFICATION = {os.getenv('ENABLE_EXTERNAL_VERIFICATION', 'NOT_SET')}")
print(f"OPENROUTER_API_KEY = {os.getenv('OPENROUTER_API_KEY', 'NOT_SET')[:20]}...")
print(f"MOCK_DB = {os.getenv('MOCK_DB', 'NOT_SET')}")
