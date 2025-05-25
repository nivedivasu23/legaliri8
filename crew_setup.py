# Import necessary libraries
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import google.generativeai as genai
from config import Config
import os

class LegalConfigSystem:
    """Enhanced YAML-based legal reference system with semantic search"""

    def __init__(self, country: str):
        self.country = country
        self.configs = self._load_all_configs()
        self.all_principles = self._flatten_principles()

    def _load_all_configs(self) -> Dict[str, Any]:
        config_path = Path(f"legal_configs/{self.country.replace(' ', '_').lower()}")
        if not config_path.exists():
            raise ValueError(f"No legal configs found for {self.country}")

        configs = {}
        for config_file in config_path.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    category = config_file.stem.replace('_', ' ').title()
                    configs[category] = yaml.safe_load(f)
                    if 'principles' not in configs[category]:
                        raise ValueError(f"Missing 'principles' in {config_file}")
            except yaml.YAMLError as e:
                print(f"Error loading {config_file}: {str(e)}")
                continue

        if not configs:
            raise ValueError(f"No valid YAML files found for {self.country}")
        return configs

    def _flatten_principles(self) -> List[Dict]:
        principles = []
        for category, config in self.configs.items():
            for principle in config['principles']:
                principle['text_searchable'] = self._create_searchable_text(principle)
                principles.append({
                    'jurisdiction': self.country,
                    'category': category,
                    **principle
                })
        return principles

    def _create_searchable_text(self, principle: Dict) -> str:
        parts = [
            principle['name'],
            principle['code'],
            principle['description'],
            ' '.join(principle.get('keywords', [])),
            ' '.join(principle.get('conditions', [])),
            ' '.join(principle.get('precedents', []))
        ]
        return ' '.join(parts).lower()

    def search_legal_references(self, query: str, category: Optional[str] = None, limit: int = 3) -> List[Dict]:
        query = query.lower()
        results = []

        keyword_matches = []
        for principle in self.all_principles:
            if category and principle['category'].lower() != category.lower():
                continue

            exact_matches = sum(
                query in field.lower()
                for field in [
                    principle['name'],
                    principle['code'],
                    ' '.join(principle.get('keywords', []))
                ]
            )

            if exact_matches > 0:
                keyword_matches.append((exact_matches, principle))

        if not keyword_matches:
            for principle in self.all_principles:
                if category and principle['category'].lower() != category.lower():
                    continue

                score = sum(
                    word in principle['text_searchable']
                    for word in query.split()
                )

                if score > 0:
                    results.append((score, principle))
        else:
            results = keyword_matches

        results.sort(reverse=True, key=lambda x: x[0])
        return [principle for score, principle in results[:limit]]

class LLMFactory:
    @staticmethod
    def get_llm(model_choice: str) -> LLM:
        config = Config()
        model_choice = model_choice.lower()

        if model_choice == "gemini":
            genai.configure(api_key=config.GOOGLE_API_KEY)
            return LLM(
                model="gemini/gemini-1.5-flash",
                config={"temperature": 0.2, "top_k": 40}
            )
        elif model_choice == "groq":
            return LLM(
                model="groq/meta-llama/llama-4-maverick-17b-128e-instruct",
            )
        raise ValueError(f"Unsupported model: {model_choice}")

def create_legal_reference_tool(country: str) -> tool:
    config_system = LegalConfigSystem(country)

    @tool
   
    def legal_reference(query: str, category: Optional[str] = None) -> str:
        """Searches YAML-based legal references for the given query and optional category."""
        try:
            references = config_system.search_legal_references(query, category)

            if not references:
                return f"No matching laws found for '{query}' in {country} {category or 'any category'}"

            formatted = []
            for ref in references:
                card = [
                    f"📜 {ref['name']} ({ref['code']})",
                    f"🏛️ Jurisdiction: {ref['jurisdiction']} | Category: {ref['category']}",
                    f"📝 Description: {ref['description']}",
                ]

                if 'conditions' in ref:
                    card.append(f"⚖️ Conditions:\n  - " + "\n  - ".join(ref['conditions']))

                if 'precedents' in ref:
                    card.append(f"👨‍⚖️ Precedents:\n  - " + "\n  - ".join(ref['precedents']))

                if 'keywords' in ref:
                    card.append(f"🔍 Keywords: {', '.join(ref['keywords'])}")

                formatted.append("\n".join(card))

            return "\n\n" + "\n\n".join(formatted) + "\n\n"
        except Exception as e:
            return f"⚠️ Error searching legal references: {str(e)}"
    return legal_reference

def create_agents(llm: LLM, country: str, rag_enabled: bool) -> List[Agent]:
    tools = []
    if rag_enabled:
        tools = [create_legal_reference_tool(country)]

    return [
        Agent(
            role=f"{country} Senior Legal Analyst",
            goal=f"Analyze cases using precise {country} legal principles",
            backstory=f"""Expert legal analyst with comprehensive knowledge of {country}'s legal system.
            Uses exact legal references from official sources.""",
            tools=tools,
            verbose=True,
            llm=llm,
            max_iter=1
        ),
        Agent(
            role=f"{country} Case Researcher",
            goal=f"Find relevant {country} laws and judicial precedents",
            backstory=f"""Legal researcher specializing in {country} jurisprudence.
            Meticulous about proper legal citations and references.""",
            tools=tools,
            verbose=True,
            llm=llm
        ),
        Agent(
            role=f"{country} Compliance Auditor",
            goal=f"Verify strict compliance with {country} legal requirements",
            backstory=f"""Legal auditor ensuring all analysis meets {country}'s legal standards.
            Expert in legal validity and proper application of laws.""",
            tools=tools,
            verbose=True,
            llm=llm
        )
    ]

def summarize_legal_yaml_with_gemini(country: str) -> str:
    config_system = LegalConfigSystem(country)
    all_principles = config_system.all_principles
    summary_chunks = []

    chunk_size = 3000
    chunk = []
    count = 0

    for principle in all_principles:
        text = f"{principle['name']} ({principle['code']}): {principle['description']}"
        if 'conditions' in principle:
            text += f"\nConditions: {'; '.join(principle['conditions'])}"
        if 'precedents' in principle:
            text += f"\nPrecedents: {'; '.join(principle['precedents'])}"
        if 'keywords' in principle:
            text += f"\nKeywords: {', '.join(principle['keywords'])}"
        chunk.append(text)

        count += 1
        if count % chunk_size == 0:
            summary_chunks.append("\n\n".join(chunk))
            chunk = []

    if chunk:
        summary_chunks.append("\n\n".join(chunk))

    genai.configure(api_key=Config().GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    summaries = []
    for chunk_text in summary_chunks:
        try:
            response = model.generate_content(f"Summarize the following legal provisions:\n\n{chunk_text}")
            summaries.append(response.text)
        except Exception as e:
            summaries.append(f"⚠️ Gemini summarization error: {str(e)}")

    return "\n\n".join(summaries)

def setup_legal_crew(case_input: str, model_choice: str, country: str, rag_enabled: bool) -> Dict:
    try:
        llm = LLMFactory.get_llm(model_choice)

        if model_choice.lower() == "groq" and rag_enabled:
            print("Summarizing YAML with Gemini for Groq...")
            summary = summarize_legal_yaml_with_gemini(country)
            case_input = f"{summary}\n\n{case_input}"

        agents = create_agents(llm, country, rag_enabled)

        # Define all required tasks
        analysis_task = Task(
            description=f"""Analyze this legal case under {country} law:
{case_input}

Required:
1. Identify exact legal provisions using proper citations
2. Reference relevant judicial precedents
3. Provide actionable legal assessment""",
            agent=agents[0],
            expected_output=f"Comprehensive legal analysis with {country} citations",
            output_file=f"{country}_analysis.md"
        )

        research_task = Task(
            description=f"""Research relevant {country} legal precedents and statutes for:
{case_input}

Required:
1. Find 3-5 most relevant cases
2. Include proper citations
3. Summarize key rulings""",
            agent=agents[1],  # Using the Case Researcher agent
            expected_output=f"List of relevant {country} case laws with summaries",
            output_file=f"{country}_research.md"
        )

        document_task = Task(
            description=f"""Prepare formal legal documentation for:
{case_input}

Required:
1. Professional legal formatting
2. Include all references
3. Use proper {country} legal terminology""",
            agent=agents[0],  # Using the Senior Legal Analyst
            expected_output="Well-structured legal document",
            output_file=f"{country}_document.md"
        )

        summary_task = Task(
            description=f"""Generate executive summary of the legal analysis for:
{case_input}

Required:
1. Maximum 3 paragraphs
2. Plain language explanation
3. Highlight key risks/opportunities""",
            agent=agents[0],  # Using the Senior Legal Analyst
            expected_output="Concise summary for non-legal audience",
            output_file=f"{country}_summary.md"
        )

        validation_task = Task(
            description=f"""Validate the legal analysis for:
1. Accuracy of {country} legal references
2. Completeness of legal arguments
3. Proper citation format""",
            agent=agents[2],  # Using the Compliance Auditor
            expected_output="Detailed compliance verification report",
            context=[analysis_task],
            output_file=f"{country}_validation.md"
        )

        crew = Crew(
            agents=agents,
            tasks=[analysis_task, research_task, document_task, summary_task, validation_task],
            process="sequential",
            verbose=True
        )

        crew_result = crew.kickoff()
        
        # Read outputs with country-specific filenames
        def read_output(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return f"{country} legal output not available"
        
        return {
            "success": True,
            "country": country,
            "report": str(crew_result),
            "analysis": read_output(f"{country}_analysis.md"),
            "research": read_output(f"{country}_research.md"),
            "document": read_output(f"{country}_document.md"),
            "summary": read_output(f"{country}_summary.md"),
            "validation": read_output(f"{country}_validation.md")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "country": country,
            "report": f"{country} legal analysis failed",
            "summary": f"Could not generate {country} legal summary"
        }