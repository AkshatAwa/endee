import os
from dotenv import load_dotenv
from .api_key_manager import check_api_key

def find_env_path(start_dir: str):
    """
    Walk up directories to find .env
    """
    curr = start_dir
    while True:
        env_path = os.path.join(curr, ".env")
        if os.path.exists(env_path):
            return env_path
        parent = os.path.dirname(curr)
        if parent == curr:
            return None
        curr = parent


# 🔍 find .env dynamically
START_DIR = os.path.dirname(__file__)
ENV_PATH = find_env_path(START_DIR)

if ENV_PATH:
    load_dotenv(dotenv_path=ENV_PATH)
    print("✅ .env loaded from:", ENV_PATH)
else:
    print("❌ .env NOT FOUND starting from:", START_DIR)


def validate_api_key(key: str) -> bool:
    if not key:
        return False

    rec = check_api_key(key)
    if rec:
        return True

    expected_key = os.getenv("LEGAL_API_KEY")
    if expected_key:
        return key == expected_key

    return False
