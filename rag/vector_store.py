from pathlib import Path
from typing import List, Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalVectorStore:
    def __init__(self, country: str):
        self.country = country.lower().replace(" ", "_")
        self.embedding_model = self._initialize_embedding_model()
        self.index_dir, self.doc_dir = self._setup_directories()
        self.index_name = f"{self.country}_legal_index"
        self.vectorstore = self._initialize_vectorstore()
        
    def _initialize_embedding_model(self):
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _setup_directories(self) -> tuple[Path, Path]:
        # Absolute path resolution
        current_file = Path(__file__).resolve()
        base_dir = current_file.parent.parent.parent  # D:\legal_crewai
        
        index_dir = base_dir / "rag" / "vector_store"
        doc_dir = base_dir / "rag" / "legal_docs" / self.country
        
        index_dir.mkdir(parents=True, exist_ok=True)
        
        if not doc_dir.exists():
            logger.warning(f"Directory created but you need to add PDFs: {doc_dir}")
            doc_dir.mkdir(parents=True, exist_ok=True)
            
        return index_dir, doc_dir

    def _initialize_vectorstore(self) -> Optional[FAISS]:
        try:
            if self._index_exists():
                logger.info(f"Loading existing index for {self.country}")
                return self._load_existing_index()
                
            logger.info(f"Creating new index for {self.country}")
            return self._create_new_index()
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return None

    def _index_exists(self) -> bool:
        return (self.index_dir / f"{self.index_name}.faiss").exists()

    def _load_existing_index(self) -> FAISS:
        return FAISS.load_local(
            folder_path=str(self.index_dir),
            embeddings=self.embedding_model,
            index_name=self.index_name,
            allow_dangerous_deserialization=True
        )

    def _create_new_index(self) -> Optional[FAISS]:
        documents = self._load_and_split_documents()
        if not documents:
            logger.error(f"Add PDFs to: {self.doc_dir}")
            return None
            
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embedding_model
        )
        self._save_index(vectorstore)
        return vectorstore

    def _load_and_split_documents(self) -> List[Document]:
        if not self.doc_dir.exists():
            return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        all_docs = []
        for filepath in self.doc_dir.glob("*.pdf"):
            if not filepath.is_file():
                continue
                
            try:
                logger.info(f"Processing: {filepath.name}")
                loader = PyPDFLoader(str(filepath))
                docs = loader.load_and_split(text_splitter)
                
                for doc in docs:
                    doc.metadata.update({
                        "country": self.country,
                        "source": filepath.name,
                        "path": str(filepath)
                    })
                
                all_docs.extend(docs)
                logger.info(f"Added {len(docs)} chunks from {filepath.name}")
                
            except Exception as e:
                logger.error(f"Failed {filepath.name}: {str(e)}")

        return all_docs

    def _save_index(self, vectorstore: FAISS):
        try:
            vectorstore.save_local(
                folder_path=str(self.index_dir),
                index_name=self.index_name
            )
            logger.info(f"Index saved for {self.country}")
        except Exception as e:
            logger.error(f"Save failed: {str(e)}")
            raise

    def retrieve_top_documents(self, query: str, k: int = 3) -> List[Dict]:
        if not self.vectorstore:
            logger.error("Initialize vectorstore first")
            return []

        try:
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            return [{
                "content": doc.page_content,
                "source": doc.metadata["source"],
                "score": float(score),
                "country": self.country
            } for doc, score in docs]
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            return []