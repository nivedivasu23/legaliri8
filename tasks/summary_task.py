from crewai import Task

def create_summary_task(agent, context):
    return Task(
        description="Create concise case summary",
        agent=agent,
        expected_output="1-2 paragraph summary",
        context=context
    )