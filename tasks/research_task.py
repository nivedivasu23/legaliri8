from crewai import Task

def create_research_task(agent, context):
    return Task(
        description="""Using RAG methodology:
        1. Research applicable laws and regulations
        2. Find relevant legal precedents from vector database
        3. Analyze strengths/weaknesses of arguments
        4. Include citations to retrieved documents""",
        agent=agent,
        expected_output="Detailed legal research with RAG references and citations",
        context=context,
        output_file="legal_research.md"
    )