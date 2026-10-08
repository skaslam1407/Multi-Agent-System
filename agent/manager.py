# Added llm below
from llm import call_llm
# Added validation below
from validation import (
    validate_task
)

# Added Logger
from logger import logger

from workers.research_agent import research
from workers.coding_agent import write_code
from workers.reviewer_agent import review
from agent.state import create_state


# Added below line
from config import (
    MAX_REVISIONS
)


# Safety cap so a confused manager LLM cannot loop forever.
# Worst case: research + coding + review per revision, plus margin.
MAX_STEPS = MAX_REVISIONS * 3 + 5



def _normalize_enabled(enabled=None):

    if enabled is None:
        return {
            "research": True,
            "coding": True,
            "review": True,
        }

    return {
        "research": bool(enabled.get("research", True)),
        "coding": bool(enabled.get("coding", True)),
        "review": bool(enabled.get("review", True)),
    }


def choose_worker(state, enabled=None):

    enabled = _normalize_enabled(enabled)

    available = [
        name for name, on in enabled.items() if on
    ] + ["finish"]

    disabled = [
        name for name, on in enabled.items() if not on
    ]

    disabled_note = (
        f"\nDisabled workers (NEVER choose these): "
        f"{', '.join(disabled)}"
        if disabled
        else ""
    )

    prompt = f"""
You are the Manager Agent.

Your job is to decide which worker
should act NEXT.
Call each agent ONLY if required.
If an agent is not required, skip it
and move forward to the next agent.

Original Task:
{state["task"]}

Research:
{state["research"]}

Code:
{state["code"]}

Review:
{state["review"]}

History:
{state["history"]}

Revision Count:
{state["revision_count"]}

Maximum Revisions:
{MAX_REVISIONS}

Enabled workers:
{", ".join(available)}
{disabled_note}

Decision rules (call each agent ONLY if required):

- Research: choose research if the task needs background, concepts,
  or examples first. SKIP it (go straight to coding) for simple,
  self-contained tasks that need no research.

- Coding: choose coding if code must be written or revised.
  SKIP it only if the task needs no code at all (pure question).

- Review: choose review if code was just written/revised and
  should be checked. SKIP it (choose finish) only for trivial
  tasks where a review adds no value.

- If a Review exists with status
  "needs_revision" and the Revision count is below the maximum
  and Coding is enabled, choose coding.

- If the latest Review status is
  "approved", choose finish.

- If the maximum revision count has
  been reached, choose finish.

- NEVER choose a disabled worker.
  NEVER choose finish while required work is missing.

Return ONLY one word:

{chr(10).join(available)}
"""
    # Modified to call_llm
    response = call_llm(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        label="Manager deciding next worker"
    )

    if not response or not response.strip():

        raise RuntimeError(
            "Manager received empty response from LLM."
        )

    cleaned = response.strip().lower()

    # LLMs often return punctuation or a sentence ("I choose coding.")
    # so extract the keyword instead of requiring an exact match.
    for keyword in (
        "research",
        "coding",
        "review",
        "finish",
    ):
        if keyword in cleaned:
            llm_choice = keyword
            break
    else:
        llm_choice = cleaned

    return apply_guardrail(llm_choice, state, enabled)


def _has_content(value):

    return bool(
        isinstance(value, str)
        and value.strip()
    )


def default_next_worker(state, enabled=None):
    """Deterministic fallback: what *should* run next.

    Disabled agents are treated as already-done (skipped).
    """

    enabled = _normalize_enabled(enabled)

    research_done = (
        not enabled["research"]
        or _has_content(state.get("research"))
    )
    code_done = (
        not enabled["coding"]
        or _has_content(state.get("code"))
    )
    review = state.get("review")
    revision_count = state.get("revision_count", 0)

    if not research_done:
        return "research"

    if not code_done:
        return "coding" if revision_count < MAX_REVISIONS else "finish"

    # Review needs code; if coding produced nothing (or coding is
    # disabled with no code), review cannot run -> finish.
    if enabled["review"]:
        if not _has_content(state.get("code")):
            return "finish"
        if not isinstance(review, dict) or not review:
            return "review"
    else:
        # Review disabled: finish once research/coding are done.
        # A stale needs_revision review can't be acted on without
        # review enabled, so just finish.
        if isinstance(review, dict) and review.get("status") == "needs_revision":
            if enabled["coding"] and revision_count < MAX_REVISIONS:
                return "coding"
        return "finish"

    status = review.get("status")

    if status == "approved":
        return "finish"

    if status == "needs_revision":
        return "coding" if (
            enabled["coding"] and revision_count < MAX_REVISIONS
        ) else "finish"

    # Unknown review shape: re-review instead of finishing blindly.
    return "review"


def apply_guardrail(llm_choice, state, enabled=None):
    """Minimal safety net for automatic agent selection.

    The manager LLM decides call-by-call which agent is required;
    if one is not required it is skipped. This only blocks
    logically impossible moves (it does NOT force the full
    research -> coding -> review chain):

    - Never pick a disabled worker.
    - Never review with no code to review.
    - Never code past MAX_REVISIONS.
    - Never finish with zero work done.
    - Never finish when the latest review explicitly demands
      revision and coding still has revisions left.
    """

    enabled = _normalize_enabled(enabled)
    valid = ("research", "coding", "review", "finish")

    if llm_choice not in valid:
        fallback = default_next_worker(state, enabled)
        logger.warning(
            f"Manager said {llm_choice!r}, "
            f"falling back to {fallback!r}."
        )
        return fallback

    # Disabled worker requested -> redirect to what should run next.
    if llm_choice != "finish" and not enabled.get(llm_choice, True):
        fallback = default_next_worker(state, enabled)
        logger.warning(
            f"Manager chose disabled worker {llm_choice!r}, "
            f"redirecting to {fallback!r}."
        )
        print(
            f"\nGuardrail: {llm_choice!r} is disabled, "
            f"using {fallback!r} instead."
        )
        return fallback

    expected = default_next_worker(state, enabled)

    if llm_choice == expected:
        return llm_choice

    has_research = _has_content(state.get("research"))
    has_code = _has_content(state.get("code"))
    review = state.get("review")
    revision_count = state.get("revision_count", 0)

    override_to = None

    if llm_choice == "review" and not has_code:
        # Nothing to review: code first (or finish if coding off).
        override_to = (
            "coding"
            if enabled.get("coding", True)
            and revision_count < MAX_REVISIONS
            else "finish"
        )
    elif llm_choice == "coding" and revision_count >= MAX_REVISIONS:
        override_to = "finish"
    elif llm_choice == "finish":
        if not has_research and not has_code:
            # Zero work done: at least do something.
            override_to = expected
        elif (
            isinstance(review, dict)
            and review.get("status") == "needs_revision"
            and enabled.get("coding", True)
            and revision_count < MAX_REVISIONS
        ):
            # Reviewer explicitly demanded a revision: don't
            # let the manager silently drop it.
            override_to = "coding"

    if override_to is not None:
        logger.warning(
            f"Guardrail: manager chose {llm_choice!r} "
            f"but {override_to!r} is required. Overriding."
        )
        print(
            f"\nGuardrail: overrode {llm_choice!r} "
            f"with {override_to!r}."
        )
        return override_to

    return llm_choice
    


def run_manager(
    task,
    enable_research=True,
    enable_coding=True,
    enable_review=True,
):
    # Added validate_task here
    task = validate_task(task)

    enabled = _normalize_enabled(
        {
            "research": enable_research,
            "coding": enable_coding,
            "review": enable_review,
        }
    )

    if not any(enabled.values()):

        raise ValueError(
            "At least one agent must be enabled."
        )

    state = create_state(
        task
    )
    # Added logger here
    logger.info(
    f"Starting manager for task: {task} | enabled: {enabled}"
    )

    print(
        "\nEnabled agents: "
        + ", ".join(
            name for name, on in enabled.items() if on
        )
        + (
            " (skipped: "
            + ", ".join(
                name for name, on in enabled.items() if not on
            )
            + ")"
            if not all(enabled.values())
            else ""
        )
    )

    # Fewer enabled agents need fewer steps.
    max_steps = max(
        5,
        sum(1 for on in enabled.values() if on) * MAX_REVISIONS + 5,
    )

    steps = 0

    while True:

        steps += 1

        if steps > max_steps:

            logger.warning(
                f"Maximum steps ({max_steps}) reached, finishing."
            )

            print(
                f"\nMaximum steps ({max_steps}) reached, finishing."
            )

            break

        worker = choose_worker(
            state,
            enabled,
        )
        # Logger added here
        logger.info(
    f"Manager selected: {worker}"
        )

        print(
            f"\nManager selected: {worker}"
        )

        # Safety net: guardrail should already block disabled
        # workers, but never execute one if it slips through.
        if worker != "finish" and not enabled.get(worker, True):

            logger.warning(
                f"Skipping disabled worker: {worker}"
            )

            print(
                f"\nSkipping disabled worker: {worker}"
            )

            continue

        if worker == "research":

            state["research"] = research(
                state["task"]
            )

            state["history"].append(
                "research"
            )

        elif worker == "coding":

            if (
            state["review"]
            and state["revision_count"]
            >= MAX_REVISIONS
            ):

                print(
                "Maximum revisions reached."
                )
                # Added Logger
                logger.warning(
        f"Maximum steps reached: {MAX_REVISIONS}"
                )


                break

            feedback = ""

            if isinstance(state["review"], dict):

                feedback = state[
                "review"
                ].get(
                "feedback",
                ""
                )

            state["revision_count"] += 1

            state["code"] = write_code(
            state["task"],
            state["research"],
            feedback
            )

            state["review"] = ""

            state["history"].append(
            "coding"
            )

        elif worker == "review":

            if not _has_content(state["code"]):

                logger.warning(
                    "Skipping review: no code to review."
                )

                print(
                    "\nSkipping review: no code to review."
                )

                state["history"].append(
                    "review_skipped"
                )

                # If coding is off and there is nothing to review,
                # there is no further work to do.
                if not enabled.get("coding", True):
                    break

                continue

            reviewed = review(
                state["task"],
                state["code"]
            )

            if (
                not isinstance(reviewed, dict)
                or reviewed.get("status") not in (
                    "approved",
                    "needs_revision",
                )
            ):

                raise ValueError(
                    f"Reviewer returned invalid result: {reviewed}"
                )

            state["review"] = reviewed

            state["history"].append(
                "review"
            )

        elif worker == "finish":
            # Added Logger here
            logger.info(
            "Manager finished the workflow."
            )

            break

        else:

            raise ValueError(
                f"Unknown worker: {worker}"
            )

    return state
