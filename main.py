import argparse

from agent.manager import run_manager

from permissions import (
    demonstrate_permissions
)



def parse_args(argv=None):

    parser = argparse.ArgumentParser(
        description="Intelligent Multi-Agent System"
    )

    parser.add_argument(
        "--task",
        default=None,
        help="Task to run (skips the interactive prompt).",
    )

    parser.add_argument(
        "--no-research",
        action="store_true",
        help="Disable the research agent.",
    )

    parser.add_argument(
        "--no-coding",
        action="store_true",
        help="Disable the coding agent.",
    )

    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Disable the reviewer agent.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show INFO logs on the console (default: warnings only).",
    )

    return parser.parse_args(argv)


def main(argv=None):

    args = parse_args(argv)

    if args.verbose:
        import logging
        for handler in logging.getLogger("agent").handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.INFO)

    print("=" * 50)
    print(" INTELLIGENT MULTI-AGENT SYSTEM")
    print("=" * 50)

    # Task: CLI flag wins, else interactive prompt.
    if args.task:

        task = args.task

    else:

        try:

            task = input(
                "\nEnter your task: "
            )

        except (EOFError, KeyboardInterrupt):

            print(
                "\nCancelled."
            )

            return

    # All agents are enabled by default. The manager LLM selects
    # automatically call-by-call: if an agent is not required for
    # the task it is skipped and the flow moves to the next agent.
    # --no-* flags optionally hard-disable an agent.
    enable_research = not args.no_research
    enable_coding = not args.no_coding
    enable_review = not args.no_review

    if not (enable_research or enable_coding or enable_review):

        print(
            "\nError: at least one agent must be enabled."
        )

        return

    try:

        state = run_manager(
            task,
            enable_research=enable_research,
            enable_coding=enable_coding,
            enable_review=enable_review,
        )

    except ValueError as e:

        print(
        f"\nError: {e}"
        )

        return

    except RuntimeError as e:

        print(
        f"\nLLM error: {e}"
        )

        return

    print("\n" + "=" * 50)
    print(" RESEARCH" + (
        "" if enable_research else " (disabled)"
    ))
    print("=" * 50)
    print(state["research"] or (
        "(disabled)" if not enable_research
        else "(skipped - not required by manager)"
    ))

    print("\n" + "=" * 50)
    print(" CODE" + (
        "" if enable_coding else " (disabled)"
    ))
    print("=" * 50)
    print(state["code"] or (
        "(disabled)" if not enable_coding
        else "(skipped - not required by manager)"
    ))

    print("\n" + "=" * 50)
    print(" REVIEW" + (
        "" if enable_review else " (disabled)"
    ))
    print("=" * 50)

    if not enable_review:

        print("(disabled)")

    else:

        review = state["review"]

        if isinstance(review, dict):
            print(f"Status: {review.get('status', 'unknown')}")
            print(f"Feedback: {review.get('feedback', '')}")
        elif review:
            print(review)
        else:
            print("(skipped - not required by manager)")

    demonstrate_permissions()


if __name__ == "__main__":
    main()
