import os

# Configurações do Ambiente Desktop
APP_NAME = "SerPleno Desktop"
APP_VERSION = "1.0.0"

API_ROOT_URL = os.getenv("SERPLENO_API_URL", "http://127.0.0.1:8000").rstrip("/")
DESKTOP_API_URL = os.getenv(
    "SERPLENO_DESKTOP_API_URL",
    f"{API_ROOT_URL}/api/v1/desktop",
).rstrip("/")
MURAL_API_URL = os.getenv(
    "SERPLENO_MURAL_API_URL",
    f"{API_ROOT_URL}/api/mural",
).rstrip("/")
