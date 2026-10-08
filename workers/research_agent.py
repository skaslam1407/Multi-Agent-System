from llm import call_llm


def research(task):

    prompt = f"""
You are a Research Agent.

Your job is to research the following task.

Task:
{task}

Provide:

1. Important concepts
2. Key facts
3. Relevant examples

Keep the response concise and useful
for another AI agent.
"""

    response = call_llm(
                messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        label="Research agent thinking"
    )

    return response
