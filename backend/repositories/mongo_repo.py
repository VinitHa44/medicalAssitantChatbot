from typing import List, Optional
from datetime import datetime
from loguru import logger

from core.database import mongodb_client
from models.database_models import QueryDocument, DocumentChunk


class QueryRepository:
    """MongoDB repository for query history"""
    
    async def save_query(
        self,
        session_id: str,
        user_query: str,
        response: str,
        sources: List[dict],
        confidence: float,
        cached: bool = False
    ) -> str:
        """Save query and response to database"""
        try:
            collection = await mongodb_client.get_queries_collection()
            
            query_doc = QueryDocument(
                session_id=session_id,
                user_query=user_query,
                response=response,
                sources=sources,
                confidence=confidence,
                cached=cached
            )
            
            result = await collection.insert_one(query_doc.to_dict())
            logger.info(f"✓ Saved query to DB: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"✗ Failed to save query: {e}")
            raise
    
    async def get_session_history(self, session_id: str) -> List[dict]:
        """Get all queries for a session"""
        try:
            collection = await mongodb_client.get_queries_collection()
            
            cursor = collection.find(
                {"session_id": session_id}
            ).sort("timestamp", 1)
            
            queries = await cursor.to_list(length=100)
            logger.info(f"✓ Retrieved {len(queries)} queries for session {session_id}")
            
            return queries
            
        except Exception as e:
            logger.error(f"✗ Failed to get session history: {e}")
            return []
    
    async def get_recent_queries(self, limit: int = 10) -> List[dict]:
        """Get recent queries across all sessions"""
        try:
            collection = await mongodb_client.get_queries_collection()
            
            cursor = collection.find().sort("timestamp", -1).limit(limit)
            queries = await cursor.to_list(length=limit)
            
            return queries
            
        except Exception as e:
            logger.error(f"✗ Failed to get recent queries: {e}")
            return []


class DocumentRepository:
    """MongoDB repository for medical documents"""
    
    async def save_document_chunks(self, chunks: List[dict]) -> int:
        """Save processed document chunks"""
        try:
            collection = await mongodb_client.get_documents_collection()
            
            # Convert to DocumentChunk objects
            chunk_docs = []
            for chunk in chunks:
                doc_chunk = DocumentChunk(
                    doc_id=chunk['doc_id'],
                    source_url=chunk['source_url'],
                    title=chunk['title'],
                    chunk_text=chunk['text'],
                    chunk_index=chunk['chunk_index'],
                    topic=chunk['topic'],
                    section=chunk.get('section', 'General'),
                    section_chunk_index=chunk.get('section_chunk_index', 0),
                    metadata={
                        'embedding_model': 'all-MiniLM-L6-v2',
                        'chunk_method': 'RecursiveCharacterTextSplitter'
                    }
                )
                chunk_docs.append(doc_chunk.to_dict())
            
            # Insert all chunks
            result = await collection.insert_many(chunk_docs)
            logger.info(f"✓ Saved {len(result.inserted_ids)} document chunks")
            
            return len(result.inserted_ids)
            
        except Exception as e:
            logger.error(f"✗ Failed to save document chunks: {e}")
            raise
    
    async def get_document_by_id(self, doc_id: str) -> Optional[dict]:
        """Get document chunk by ID"""
        try:
            collection = await mongodb_client.get_documents_collection()
            doc = await collection.find_one({"doc_id": doc_id})
            return doc
            
        except Exception as e:
            logger.error(f"✗ Failed to get document: {e}")
            return None
    
    async def get_documents_by_topic(self, topic: str) -> List[dict]:
        """Get all document chunks for a topic"""
        try:
            collection = await mongodb_client.get_documents_collection()
            
            cursor = collection.find({"topic": topic})
            docs = await cursor.to_list(length=1000)
            
            logger.info(f"✓ Retrieved {len(docs)} documents for topic: {topic}")
            return docs
            
        except Exception as e:
            logger.error(f"✗ Failed to get documents by topic: {e}")
            return []
    
    async def count_documents(self) -> dict:
        """Get document statistics"""
        try:
            collection = await mongodb_client.get_documents_collection()
            
            total = await collection.count_documents({})
            
            # Get all unique topics using aggregation
            pipeline = [
                {"$group": {"_id": "$topic", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            topics = {result["_id"]: result["count"] for result in results}
            
            return {
                "total": total,
                "by_topic": topics
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to count documents: {e}")
            return {"total": 0, "by_topic": {}}


# Singleton instances
query_repo = QueryRepository()
document_repo = DocumentRepository()
