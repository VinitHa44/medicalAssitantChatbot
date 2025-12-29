from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional
from loguru import logger
from config import settings
import time


class VectorDatabase:
    """Manages Pinecone vector database"""
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def create_index(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                
                logger.info(f"✓ Index {self.index_name} created")
            else:
                logger.info(f"✓ Index {self.index_name} already exists")
            
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"✗ Failed to create index: {e}")
            raise
    
    def upsert_documents(self, chunks: List[Dict], batch_size: int = 100):
        """Upload document chunks to Pinecone"""
        if not self.index:
            self.create_index()
        
        vectors = []
        for chunk in chunks:
            vector = {
                'id': chunk['doc_id'],
                'values': chunk['embedding'],
                'metadata': {
                    'text': chunk['text'][:1000],  # Pinecone metadata limit
                    'source_url': chunk['source_url'],
                    'title': chunk['title'],
                    'topic': chunk['topic'],
                    'section': chunk.get('section', 'General'),
                    'chunk_index': chunk['chunk_index'],
                    'section_chunk_index': chunk.get('section_chunk_index', 0)
                }
            }
            vectors.append(vector)
        
        # Upsert in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"✓ Upserted batch {i//batch_size + 1} ({len(batch)} vectors)")
        
        logger.info(f"✓ Total vectors upserted: {len(vectors)}")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        topic_filter: Optional[str] = None,
        section_filter: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar documents with optional section filtering"""
        if not self.index:
            self.create_index()
        
        top_k = top_k or settings.TOP_K_RESULTS
        
        # Build filter
        filter_dict = {}
        if topic_filter:
            filter_dict['topic'] = topic_filter
        if section_filter:
            filter_dict['section'] = section_filter
        
        # Query
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        # Format results
        matches = []
        for match in results['matches']:
            matches.append({
                'id': match['id'],
                'score': match['score'],
                'text': match['metadata']['text'],
                'source_url': match['metadata']['source_url'],
                'title': match['metadata']['title'],
                'topic': match['metadata']['topic'],
                'section': match['metadata'].get('section', 'General'),
                'chunk_index': match['metadata'].get('chunk_index', 0)
            })
        
        logger.info(f"✓ Found {len(matches)} matches")
        return matches
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        if not self.index:
            self.create_index()
        
        stats = self.index.describe_index_stats()
        return {
            'total_vectors': stats.total_vector_count,
            'dimension': stats.dimension,
            'index_fullness': stats.index_fullness
        }
    
    def delete_all(self):
        """Delete all vectors (use with caution)"""
        if self.index:
            self.index.delete(delete_all=True)
            logger.warning("⚠ Deleted all vectors from index")


vector_db = VectorDatabase()
