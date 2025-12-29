"""
Data Pipeline Script
Scrapes medical articles, processes them, and indexes to Pinecone
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from services.scraper import scrape_medical_data
from services.text_processor import text_processor
from services.vector_store import vector_db
from repositories.mongo_repo import document_repo


async def run_data_pipeline():
    """
    Complete data pipeline:
    1. Scrape medical articles
    2. Process and chunk text
    3. Create embeddings
    4. Index to Pinecone
    5. Save to MongoDB
    """
    
    logger.info("=" * 60)
    logger.info("STARTING DATA PIPELINE")
    logger.info("=" * 60)
    
    # Step 1: Scrape medical data
    logger.info("\n[1/5] Scraping medical articles...")
    scraped_docs = scrape_medical_data()
    logger.info(f"✓ Scraped {len(scraped_docs)} articles")
    
    # Step 2: Process documents
    logger.info("\n[2/5] Processing and chunking documents...")
    all_chunks = []
    
    for doc in scraped_docs:
        chunks = text_processor.process_document(doc)
        all_chunks.extend(chunks)
    
    logger.info(f"✓ Created {len(all_chunks)} total chunks")
    
    # Step 3: Create Pinecone index
    logger.info("\n[3/5] Setting up Pinecone index...")
    vector_db.create_index()
    logger.info("✓ Index ready")
    
    # Step 4: Upload to Pinecone
    logger.info("\n[4/5] Uploading embeddings to Pinecone...")
    vector_db.upsert_documents(all_chunks)
    logger.info("✓ Embeddings indexed")
    
    # Step 5: Save to MongoDB
    logger.info("\n[5/5] Saving documents to MongoDB...")
    count = await document_repo.save_document_chunks(all_chunks)
    logger.info(f"✓ Saved {count} chunks to MongoDB")
    
    # Show stats
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE - STATISTICS")
    logger.info("=" * 60)
    
    pinecone_stats = vector_db.get_stats()
    mongo_stats = await document_repo.count_documents()
    
    logger.info(f"Pinecone vectors: {pinecone_stats['total_vectors']}")
    logger.info(f"MongoDB documents: {mongo_stats['total']}")
    logger.info(f"Topics: {list(mongo_stats['by_topic'].keys())}")
    
    for topic, count in mongo_stats['by_topic'].items():
        logger.info(f"  - {topic}: {count} chunks")
    
    logger.info("\n✓ Knowledge base ready for RAG queries!")


if __name__ == "__main__":
    asyncio.run(run_data_pipeline())
