TOOL_PERMISSIONS = {

    "research": {
        "get_weather",
        "read_file"
    },

    "coding": {
        "read_file"
    },

    "review": {
        "read_file"
    },

    "manager": {
        "get_weather",
        "read_file"
    }
}


def is_tool_allowed(
    agent_name,
    tool_name
):

    allowed_tools = (
        TOOL_PERMISSIONS.get(
            agent_name,
            set()
        )
    )

    return (
        tool_name in allowed_tools
    )

def demonstrate_permissions():

    examples = [
        ("research", "read_file"),
        ("coding", "get_weather"),
        ("review", "read_file"),
        ("manager", "get_weather")
    ]

    print("\nPermission Demonstration")
    print("-" * 30)

    for agent_name, tool_name in examples:

        allowed = is_tool_allowed(
            agent_name,
            tool_name
        )

        print(
            f"{agent_name:10} -> "
            f"{tool_name:12} : "
            f"{'ALLOWED' if allowed else 'DENIED'}"
        )

