from typing import List, Dict, Optional
from loguru import logger

from services.text_processor import text_processor
from services.vector_store import vector_db
from services.llm import llm_service
from models.schemas import Source


class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        logger.info("✓ RAG Pipeline initialized")
    
    async def query(
        self,
        user_query: str,
        top_k: int = 10,
        topic_filter: Optional[str] = None
    ) -> Dict:
        """
        Execute RAG pipeline
        
        Flow:
        1. Embed user query
        2. Search vector database
        3. Retrieve top-K chunks
        4. Generate response with LLM
        5. Format and return
        """
        
        # Ensure top_k is an integer
        top_k = int(top_k) if top_k else 3
        
        logger.info(f"RAG Query: {user_query[:100]}...")
        
        # Step 1: Create query embedding
        query_embedding = text_processor.create_embedding(user_query)
        logger.info("✓ Query embedded")
        
        # Step 2: Search vector database
        matches = vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k,
            topic_filter=topic_filter
        )
        
        if not matches:
            logger.warning("No matches found in vector database")
            return {
                'response': "I don't have specific information about that topic in my current knowledge base. My knowledge covers diabetes, hypertension, and related cardiovascular conditions. Please try asking about these topics, or consult a healthcare professional for information on other medical subjects.",
                'sources': [],
                'confidence': 0.0
            }
        
        # Step 3: Generate response with LLM
        llm_result = llm_service.generate_response(
            query=user_query,
            context_chunks=matches,
            use_chain_of_thought=True
        )
        
        # Step 4: Format sources
        sources = self._extract_sources(matches)
        
        result = {
            'response': llm_result['response'],
            'sources': sources,
            'confidence': llm_result['confidence'],
            'emergency': llm_result.get('emergency', False)
        }
        
        logger.info(f"✓ RAG complete (confidence: {result['confidence']:.2f})")
        return result
    
    @staticmethod
    def _extract_sources(matches: List[Dict]) -> List[Source]:
        """Extract and deduplicate sources"""
        seen_urls = set()
        sources = []
        
        for match in matches:
            url = match['source_url']
            if url not in seen_urls:
                sources.append(Source(
                    url=url,
                    title=match.get('title'),
                    relevance_score=match['score']
                ))
                seen_urls.add(url)
        
        return sources


rag_pipeline = RAGPipeline()
