from llm import call_llm

def write_code(
    task,
    research,
    feedback=""
):

    prompt = f"""
You are a Coding Agent.

Write or revise Python code based on
the task and research.

Task:
{task}

Research:
{research}

Previous Reviewer Feedback:
{feedback}

If reviewer feedback is provided,
correct the identified problems.

Return:

1. Short explanation
2. Complete Python code
"""

    response = call_llm(
            messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        label="Coding agent thinking"
    )

    return response

