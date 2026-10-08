"""Terminal spinner shown while the LLM is thinking.

Usage:
    from animation import thinking

    with thinking("Research agent thinking"):
        response = client.chat.completions.create(...)

The spinner runs on a background thread so the blocking LLM call
does not freeze the UI. It is automatically stopped on success
or exception. Set NO_ANIMATION=1 to disable (e.g. tests / logs).
"""

import itertools
import os
import sys
import threading
import time


_FRAMES = ["|", "/", "-", "\\"]

_DISABLED = os.getenv("NO_ANIMATION", "").lower() in ("1", "true", "yes")


class thinking:
    def __init__(self, message="LLM thinking"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None
        self._enabled = not _DISABLED and sys.stdout.isatty()

    def _spin(self):
        frames = itertools.cycle(_FRAMES)
        while not self._stop_event.is_set():
            frame = next(frames)
            sys.stdout.write(f"\r{frame} {self.message}...")
            sys.stdout.flush()
            # wait() instead of sleep() so we stop immediately
            self._stop_event.wait(0.1)
        # clear the spinner line
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        if self._enabled:
            self._thread = threading.Thread(
                target=self._spin, daemon=True
            )
            self._thread.start()
        elif self.message:
            # Non-TTY fallback: single static line so user still
            # sees progress in logs / piped output.
            sys.stdout.write(f"{self.message}...\n")
            sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._enabled and self._thread is not None:
            self._stop_event.set()
            self._thread.join(timeout=1.0)
        # Do not suppress exceptions
        return False
