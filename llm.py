import time

from openai import OpenAI

from config import (
    BASE_URL,
    API_KEY,
    MODEL,
    MAX_RETRIES,
    TIMEOUT
)

from logger import logger

from animation import thinking


client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=TIMEOUT
)


def call_llm(messages, label="LLM thinking"):

    retries = max(1, MAX_RETRIES)

    for attempt in range(
        1,
        retries + 1
    ):

        try:

            logger.info(
                f"LLM request attempt {attempt}"
            )

            with thinking(
                f"{label} (attempt {attempt}/{retries})"
            ):

                response = (
                    client
                    .chat
                    .completions
                    .create(
                        model=MODEL,
                        messages=messages
                    )
                )

            logger.info(
                "LLM request successful"
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if content is None or not content.strip():

                raise RuntimeError(
                    "LLM returned empty response."
                )

            return content

        except Exception as e:

            logger.error(
                f"LLM request failed: {e}"
            )

            if attempt == retries:

                logger.error(
                    "Maximum retry limit reached"
                )

                raise RuntimeError(
                    "LLM request failed after "
                    f"{retries} attempts."
                ) from e

            wait_time = attempt * 2

            logger.info(
                f"Retrying in {wait_time} seconds"
            )

            time.sleep(
                wait_time
            )
