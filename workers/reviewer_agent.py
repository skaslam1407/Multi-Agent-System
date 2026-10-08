from llm import call_llm
import json
def review(
    task,
    code
):

    prompt = f"""
You are a Reviewer Agent.

Review the following Python solution.

Task:
{task}

Solution:
{code}

Check:

1. Correctness
2. Python syntax
3. Logic
4. Missing issues
5. Possible improvements

Return ONLY valid JSON.

Use exactly this format:

{{
    "status": "approved",
    "feedback": "The solution is correct."
}}

OR:

{{
    "status": "needs_revision",
    "feedback": "Explain what needs to be changed."
}}

Use "approved" only when the solution
is acceptable.

Use "needs_revision" when the solution
requires a correction.
"""

    response = call_llm(
                messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        label="Reviewer agent thinking"
    )

    result = response.strip()

    # Strip markdown code fences like ```json ... ``` which LLMs often add
    if result.startswith("```"):
        # Remove first fence line
        lines = result.splitlines()
        # Drop opening ```json / ``` line
        lines = lines[1:]
        # Drop closing ``` if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        result = "\n".join(lines).strip()

    # If the model wrapped JSON in prose ("Here is the JSON: {...}"),
    # extract the first {...} block.
    if not result.startswith("{"):
        start = result.find("{")
        end = result.rfind("}")
        if start != -1 and end != -1 and end > start:
            result = result[start:end + 1].strip()

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Reviewer returned invalid JSON: {e}\nRaw output: {response}"
        )

    if not isinstance(parsed, dict):
        raise ValueError(
            f"Reviewer must return a JSON object, got: {response}"
        )

    status = str(parsed.get("status", "")).strip().lower()
    feedback = str(parsed.get("feedback", "")).strip()

    if status not in ("approved", "needs_revision"):
        raise ValueError(
            f"Reviewer returned unknown status {status!r}. "
            f"Raw output: {response}"
        )

    return {
        "status": status,
        "feedback": feedback,
    }

