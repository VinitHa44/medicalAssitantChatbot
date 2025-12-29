from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from loguru import logger
from config import settings
import hashlib


class TextProcessor:
    """Processes and chunks text for embedding"""
    
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("✓ Text processor initialized")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep medical terms
        # (Keep hyphens, parentheses for medical notation)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into chunks"""
        cleaned = self.clean_text(text)
        chunks = self.splitter.split_text(cleaned)
        
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_obj = {
                'text': chunk,
                'chunk_index': i,
                'metadata': metadata or {}
            }
            chunk_objects.append(chunk_obj)
        
        logger.info(f"✓ Created {len(chunk_objects)} chunks")
        return chunk_objects
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    
    @staticmethod
    def generate_doc_id(url: str, chunk_index: int) -> str:
        """Generate unique document ID"""
        content = f"{url}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def process_document(self, doc: Dict) -> List[Dict]:
        """Process a scraped document into chunks with embeddings and section info"""
        
        # Check if document has section information
        if 'sections' in doc and doc['sections']:
            return self._process_document_with_sections(doc)
        else:
            return self._process_document_legacy(doc)
    
    def _process_document_with_sections(self, doc: Dict) -> List[Dict]:
        """Process document with section information"""
        all_chunks = []
        global_chunk_index = 0
        
        for section_data in doc['sections']:
            section_name = section_data['section']
            section_content = section_data['content']
            
            # Chunk the section content
            chunks = self.chunk_text(
                section_content,
                metadata={
                    'url': doc['url'],
                    'title': doc['title'],
                    'topic': doc.get('topic', 'general'),
                    'section': section_name
                }
            )
            
            # Generate embeddings for this section's chunks
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.create_embeddings_batch(texts)
            
            # Create processed chunks
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                processed_chunk = {
                    'doc_id': self.generate_doc_id(doc['url'], global_chunk_index),
                    'text': chunk['text'],
                    'embedding': embedding,
                    'source_url': doc['url'],
                    'title': doc['title'],
                    'topic': doc.get('topic', 'general'),
                    'section': section_name,
                    'chunk_index': global_chunk_index,
                    'section_chunk_index': i
                }
                all_chunks.append(processed_chunk)
                global_chunk_index += 1
        
        logger.info(f"✓ Processed {len(all_chunks)} chunks across {len(doc['sections'])} sections")
        return all_chunks
    
    def _process_document_legacy(self, doc: Dict) -> List[Dict]:
        """Process document without section information (legacy method)"""
        chunks = self.chunk_text(
            doc['content'],
            metadata={
                'url': doc['url'],
                'title': doc['title'],
                'topic': doc.get('topic', 'general')
            }
        )
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.create_embeddings_batch(texts)
        
        # Combine chunks with embeddings
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            processed_chunk = {
                'doc_id': self.generate_doc_id(doc['url'], i),
                'text': chunk['text'],
                'embedding': embedding,
                'source_url': doc['url'],
                'title': doc['title'],
                'topic': doc.get('topic', 'general'),
                'section': 'General',
                'chunk_index': i,
                'section_chunk_index': i
            }
            processed_chunks.append(processed_chunk)
        
        logger.info(f"✓ Processed {len(processed_chunks)} chunks with embeddings")
        return processed_chunks


text_processor = TextProcessor()
