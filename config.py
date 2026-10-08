import os

from dotenv import load_dotenv


load_dotenv()


MODEL = os.getenv(
    "MODEL",
    "qwen3:1.7b"
)


BASE_URL = os.getenv(
    "BASE_URL",
    "http://localhost:11434/v1"
)


API_KEY = os.getenv(
    "API_KEY",
    "ollama"
)


def _get_int(name, default):

    try:

        return int(
            os.getenv(name, str(default))
        )

    except (ValueError, TypeError):

        return default


MAX_REVISIONS = _get_int(
    "MAX_REVISIONS",
    8
)


MAX_RETRIES = _get_int(
    "MAX_RETRIES",
    3
)


TIMEOUT = _get_int(
    "TIMEOUT",
    60
)

