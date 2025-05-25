from rag.vector_store import LegalVectorStore
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalRetriever:
    def __init__(self, country: str):
        self.country = country.lower()
        try:
            self.vector_store = LegalVectorStore(country)
            logger.info(f"Initialized retriever for {country}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    def retrieve_country_laws(self, case_text: str, n_results: int = 3) -> List[Dict]:
        """Retrieve laws specific to the initialized country"""
        try:
            query = f"{self.country} legal principles relevant to: {case_text}"
            results = self.vector_store.retrieve_top_documents(query, n_results)
            
            if not results:
                logger.warning(f"No results found for {self.country} query: {query[:50]}...")
                return []
            
            # Filter and format results
            formatted_results = []
            for doc in results:
                if not isinstance(doc, dict):
                    logger.warning(f"Unexpected document format: {type(doc)}")
                    continue
                
                formatted_results.append({
                    "content": doc.get("content", ""),
                    "source": doc.get("source", "Unknown"),
                    "score": doc.get("score", 0.0),
                    "country": self.country
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            return []

    def format_for_agent(self, case_text: str, n_results: int = 3) -> str:
        """Format results for agent consumption"""
        retrieved = self.retrieve_country_laws(case_text, n_results)
        if not retrieved:
            return f"No specific {self.country} laws found for this case"
            
        context = "\n\n".join(
            f"SOURCE: {doc['source']}\nCONTENT:\n{doc['content']}" 
            for doc in retrieved
        )
        return f"""
        {self.country.upper()} LEGAL CONTEXT:
        {context}
        """