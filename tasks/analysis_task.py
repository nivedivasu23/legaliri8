from crewai import Task

def create_analysis_task(case_input, agent):
    return Task(
        description=f"""Analyze this legal case:
        1. Key facts and parties
        2. Legal domains
        3. Potential issues
        
        Case: {case_input}""",
        agent=agent,
        expected_output="Structured case analysis"
    )