def validate_task(task):

    if task is None:

        raise ValueError(
            "Task cannot be empty."
        )

    if not isinstance(task, str):

        raise ValueError(
            "Task must be a string."
        )

    task = task.strip()

    if not task:

        raise ValueError(
            "Task cannot be empty."
        )

    if len(task) > 5000:

        raise ValueError(
            "Task is too long."
        )

    return task
