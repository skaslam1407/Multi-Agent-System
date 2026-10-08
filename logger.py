import logging
import os


LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
LOG_FILE = os.getenv("LOG_FILE", "agent.log")

# Console stays clean (only warnings/errors) so log lines never
# mix into the LLM response output. Full INFO history goes to file.
logger = logging.getLogger(
    "agent"
)
logger.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    "%(asctime)s | "
    "%(levelname)s | "
    "%(message)s"
)

_console = logging.StreamHandler()
_console.setLevel(getattr(logging, LOG_LEVEL, logging.WARNING))
_console.setFormatter(_formatter)

_file = logging.FileHandler(LOG_FILE)
_file.setLevel(logging.DEBUG)
_file.setFormatter(_formatter)

# Avoid duplicate handlers on re-import.
if not logger.handlers:
    logger.addHandler(_console)
    logger.addHandler(_file)

logger.propagate = False

# Silence noisy third-party INFO logs (openai/httpx) that used to
# pollute the console, e.g. "HTTP Request: POST ... 200 OK".
for _noisy in ("openai", "httpx", "httpcore", "urllib3"):
    _lg = logging.getLogger(_noisy)
    _lg.setLevel(logging.WARNING)
    _lg.propagate = False
