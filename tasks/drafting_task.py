from crewai import Task

def create_drafting_task(agent, context):
    return Task(
        description="Create comprehensive legal case study",
        agent=agent,
        expected_output="Professional case study document",
        context=context
    )   