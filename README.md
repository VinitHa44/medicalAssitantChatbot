# Medical Assistant Chatbot - Backend

MVP Backend for medical domain chatbot with RAG, voice capabilities, and Digital Twin persona.

## 📋 Technical Documentation

### High-Level Design (HLD)

#### System Overview
The Medical Assistant Chatbot is a RAG-based conversational AI system designed to provide reliable medical information using a Digital Twin persona (Dr. Asha). The system leverages multiple cloud services, databases, and AI models to deliver accurate, context-aware responses.

#### Core Components
1. **API Layer**: FastAPI-based REST endpoints for text and voice interactions
2. **RAG Pipeline**: Retrieval-Augmented Generation for context-aware responses
3. **Vector Search**: Pinecone for semantic similarity matching
4. **LLM Engine**: Meta Llama 3.3 70B (via Groq API) for response generation
5. **Caching Layer**: Redis for performance optimization
6. **Persistent Storage**: MongoDB for chat history and documents
7. **Voice Processing**: Whisper (STT) + Coqui TTS for voice interactions
8. **Digital Twin**: Dr. Asha persona for empathetic medical guidance

#### Technology Stack
- **Framework**: FastAPI (async Python web framework)
- **LLM**: Meta Llama 3.3 70B Versatile (via Groq API, Chain of Thought reasoning)
- **Vector DB**: Pinecone (cloud-native vector database)
- **Database**: MongoDB (document store for chat history)
- **Cache**: Redis (in-memory cache, TTL: 1 hour)
- **Voice STT**: OpenAI Whisper (speech-to-text)
- **Voice TTS**: Coqui TTS (text-to-speech)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384-dim vectors)

---

### Low-Level Design (LLD)

#### 1. API Routes Layer (`api/routes/`)

**chat.py - Text Chat Endpoint**
```
POST /api/chat/text
├─ Input: ChatRequest (query, session_id)
├─ Process:
│  ├─ Check Redis cache (cache_manager.get)
│  ├─ If HIT: Return cached response
│  ├─ If MISS:
│  │  ├─ Execute RAG pipeline
│  │  ├─ Save to MongoDB (query_repo.save_query)
│  │  └─ Cache result (cache_manager.set, TTL=3600s)
└─ Output: ChatResponse (response, sources, confidence, cached)
```

**voice.py - Voice Chat Endpoint**
```
POST /api/chat/voice
├─ Input: Audio file (multipart/form-data) + session_id
├─ Process:
│  ├─ Save audio to temp directory
│  ├─ Transcribe audio → text (Whisper)
│  ├─ Check cache with transcribed query
│  ├─ If MISS: Run RAG pipeline
│  ├─ Generate TTS audio response
│  ├─ Save to MongoDB
│  └─ Cache result
└─ Output: ChatResponse + audio_url + transcribed_query
```

**health.py - Health Check**
```
GET /api/health
├─ Check:
│  ├─ Redis connection (ping)
│  ├─ MongoDB connection (ping)
│  └─ Pinecone status
└─ Output: Service status + uptime
```

#### 2. Core Layer (`core/`)

**database.py - Connection Managers**
```python
MongoDB:
  - AsyncIOMotorClient (motor library)
  - Collections: queries, documents
  - Methods: get_queries_collection(), get_documents_collection()

RedisCache:
  - Redis async client
  - decode_responses=True (JSON serialization)
  - Methods: connect(), close(), ping()
```

**cache.py - Cache Manager**
```python
CacheManager:
  - _generate_key(query, session_id):
      → MD5 hash of "query:session_id"
      → Prefix: "chat:{hash}"
  
  - get(query, session_id):
      → Retrieve from Redis
      → JSON deserialize
      → Returns: {response, sources, confidence} or None
  
  - set(query, response, session_id):
      → JSON serialize
      → SETEX with TTL=3600 (1 hour)
      → Returns: bool (success)
  
  - clear_session(session_id):
      → Pattern match: "chat:*:{session_id}"
      → Delete all matching keys
```

**persona.py - Dr. Asha Digital Twin**
```python
SYSTEM_PROMPT:
  - Role: Empathetic medical assistant
  - Constraints: No diagnosis, no prescriptions
  - Safety: Emergency detection, disclaimers
  - Style: Clear, compassionate, evidence-based

CHAIN_OF_THOUGHT_PROMPT:
  - Structured reasoning template
  - Evidence analysis
  - Confidence estimation
  - Emergency detection
```

#### 3. Services Layer (`services/`)

**rag.py - RAG Pipeline**
```python
RAGPipeline.query(user_query, top_k, topic_filter):
  1. Embed query (text_processor.create_embedding)
     → 384-dim vector
  
  2. Vector search (vector_db.search)
     → Pinecone similarity search
     → Return top-K matches (default K=3)
  
  3. Generate response (llm_service.generate_response)
     → Context chunks + query → Llama 3
     → Chain of Thought reasoning
  
  4. Extract sources (_extract_sources)
     → Deduplicate URLs
     → Return Source objects
  
  5. Return: {response, sources, confidence, emergency}
```

**llm.py - Llama 3 LLM Service**
```python
LLMService.generate_response(query, context_chunks, use_chain_of_thought):
  1. Format context from chunks
  2. Build prompt:
     - SYSTEM_PROMPT (Dr. Asha persona)
     - CHAIN_OF_THOUGHT_PROMPT (if enabled)
     - Context chunks
     - User query
  
  3. Call Groq API:
     - Model: llama-3.3-70b-versatile
     - Temperature: 0.7
     - Max tokens: 1024
  
  4. Parse response:
     - Extract reasoning, response, confidence
     - Detect emergency keywords
  
  5. Return: {response, confidence, emergency, reasoning}
```

**vector_store.py - Pinecone Integration**
```python
VectorStore:
  - Index: "medical-chatbot"
  - Dimension: 384
  - Metric: cosine similarity
  
  - search(query_embedding, top_k, topic_filter):
      → Pinecone query with filters
      → Returns: [{id, score, metadata}]
  
  - upsert(vectors, metadata):
      → Batch insert with metadata
      → Metadata: {text, source_url, title, topic}
```

**text_processor.py - Embedding & Chunking**
```python
TextProcessor:
  - Model: sentence-transformers/all-MiniLM-L6-v2
  
  - chunk_text(text, chunk_size=2000, overlap=200):
      → Recursive character splitting
      → Preserves paragraphs/sentences
      → Returns: List[str]
  
  - create_embedding(text):
      → Encode with sentence-transformer
      → Returns: np.array (384-dim)
  
  - batch_embed(texts):
      → Batch processing for efficiency
      → Returns: List[np.array]
```

**scraper.py - Web Scraper**
```python
MedicalScraper:
  - Sources: WHO, Mayo Clinic, CDC
  - Libraries: BeautifulSoup4, requests
  
  - scrape_url(url):
      → Extract article content
      → Clean HTML tags
      → Extract title, metadata
      → Returns: {url, title, content}
  
  - scrape_all():
      → Parallel scraping (ThreadPoolExecutor)
      → Error handling & retries
      → Returns: List[Document]
```

**voice.py - Voice Processing**
```python
VoiceService:
  - STT Model: Whisper (base)
  - TTS Model: Coqui TTS (tacotron2)
  
  - transcribe_audio(audio_path):
      → Load audio file
      → Whisper.transcribe()
      → Returns: {text, language, confidence}
  
  - text_to_speech(text, session_id):
      → Generate audio with TTS
      → Save to static/audio/{session_id}.wav
      → Returns: audio_url
```

#### 4. Repositories Layer (`repositories/`)

**mongo_repo.py - MongoDB Operations**
```python
QueryRepository:
  - save_query(session_id, user_query, response, sources, confidence, cached):
      → Insert to queries collection
      → Timestamp: UTC
      → Returns: inserted_id
  
  - get_history(session_id, limit=50):
      → Find by session_id
      → Sort: timestamp DESC
      → Returns: List[QueryDocument]
  
  - get_stats():
      → Aggregation pipeline
      → Returns: {total_queries, cache_hit_rate, avg_confidence}
```

#### 5. Models Layer (`models/`)

**schemas.py - Pydantic Models**
```python
ChatRequest:
  - query: str (max_length=500)
  - session_id: str

ChatResponse:
  - response: str
  - sources: List[Source]
  - confidence: float (0.0-1.0)
  - cached: bool
  - audio_url: Optional[str]
  - transcribed_query: Optional[str]

Source:
  - url: str
  - title: Optional[str]
  - relevance_score: float
```

**database_models.py - MongoDB Models**
```python
QueryDocument:
  - _id: ObjectId
  - session_id: str
  - user_query: str
  - response: str
  - sources: List[dict]
  - confidence: float
  - cached: bool
  - timestamp: datetime
  - emergency: bool
```

---

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  Web Frontend    │              │  Voice Client    │            │
│  │  (React/Vite)    │              │  (Microphone)    │            │
│  └────────┬─────────┘              └────────┬─────────┘            │
│           │                                  │                       │
│           └──────────────────┬───────────────┘                       │
└───────────────────────────────┼───────────────────────────────────┘
                                │ HTTP/REST API
┌───────────────────────────────┼───────────────────────────────────┐
│                         API GATEWAY LAYER                           │
│                    ┌──────────▼──────────┐                          │
│                    │   FastAPI Server    │                          │
│                    │   (main.py)         │                          │
│                    └──────────┬──────────┘                          │
│                               │                                      │
│         ┌─────────────────────┼─────────────────────┐              │
│         │                     │                     │              │
│    ┌────▼─────┐        ┌─────▼──────┐      ┌──────▼─────┐        │
│    │ /chat    │        │  /voice    │      │  /health   │        │
│    │  /text   │        │            │      │            │        │
│    └────┬─────┘        └─────┬──────┘      └──────┬─────┘        │
└─────────┼────────────────────┼────────────────────┼───────────────┘
          │                    │                    │
┌─────────┼────────────────────┼────────────────────┼───────────────┐
│         │         BUSINESS LOGIC LAYER            │               │
│         │                    │                    │               │
│    ┌────▼────────────────────▼────┐         ┌────▼──────┐        │
│    │    Cache Manager (Redis)     │         │  Health   │        │
│    │  ┌──────────────────────┐    │         │  Checks   │        │
│    │  │ HIT → Return Cached  │    │         └───────────┘        │
│    │  └──────────┬───────────┘    │                               │
│    │             │ MISS            │                               │
│    └─────────────┼─────────────────┘                               │
│                  │                                                  │
│         ┌────────▼────────┐                                        │
│         │   RAG Pipeline  │                                        │
│         │                 │                                        │
│         │  1. Embed Query ├────► Text Processor                   │
│         │                 │      (sentence-transformers)           │
│         │  2. Vector      ├────► Pinecone Vector DB               │
│         │     Search      │      (similarity search)               │
│         │                 │                                        │
│         │  3. LLM Gen     ├────► Llama 3.3 70B                    │
│         │                 │      (Chain of Thought)                │
│         │  4. Persona     ├────► Dr. Asha Formatter               │
│         │                 │                                        │
│         └────────┬────────┘                                        │
│                  │                                                  │
│         ┌────────▼────────┐                                        │
│         │  Voice Service  │                                        │
│         │  (if voice req) │                                        │
│         │                 │                                        │
│         │  ┌──────────┐   │                                        │
│         │  │ Whisper  │   │  (STT)                                 │
│         │  └──────────┘   │                                        │
│         │  ┌──────────┐   │                                        │
│         │  │Coqui TTS │   │  (TTS)                                 │
│         │  └──────────┘   │                                        │
│         └─────────────────┘                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────┼─────────────────────────────────────┐
│                      DATA PERSISTENCE LAYER                         │
│                              │                                      │
│   ┌──────────────┐    ┌─────▼──────┐    ┌─────────────────┐      │
│   │   Redis      │    │  MongoDB   │    │   Pinecone      │      │
│   │  (Cache)     │    │ (History)  │    │ (Vector Index)  │      │
│   │              │    │            │    │                 │      │
│   │ • TTL: 1hr   │    │ • queries  │    │ • 384-dim       │      │
│   │ • JSON data  │    │ • documents│    │ • Cosine sim    │      │
│   │ • Session    │    │ • Session  │    │ • Metadata      │      │
│   │   based      │    │   history  │    │   filtering     │      │
│   └──────────────┘    └────────────┘    └─────────────────┘      │
└──────────────────────────────────────────────────────────────────┘

External Services:
┌───────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│  Groq API         │  │    Pinecone      │  │  HuggingFace       │
│  (Llama 3)        │  │    Cloud API     │  │  (Embeddings)      │
└───────────────────┘  └──────────────────┘  └────────────────────┘
```

---

### Data Flow Diagram

#### **Text Chat Flow**
```
┌──────────┐
│  User    │
│  Query   │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ POST /api/chat/text                 │
│ {query, session_id}                 │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Cache Check (Redis)                 │
│ Key: MD5(query:session_id)          │
└────┬────────────────────────────────┘
     │
     ├─── HIT ───► Return Cached ────┐
     │             (50-100ms)         │
     │                                │
     └─── MISS                        │
          │                           │
          ▼                           │
     ┌─────────────────────┐         │
     │ 1. Text Processor   │         │
     │    Embed Query      │         │
     │    → 384-dim vector │         │
     └──────┬──────────────┘         │
            │                         │
            ▼                         │
     ┌─────────────────────┐         │
     │ 2. Pinecone Search  │         │
     │    Vector Similarity│         │
     │    → Top-K=3 chunks │         │
     └──────┬──────────────┘         │
            │                         │
            ▼                         │
     ┌─────────────────────┐         │
     │ 3. LLM Generation   │         │
     │    Llama 3.3 70B    │         │
     │    + Chain of       │         │
     │      Thought        │         │
     │    + Dr. Asha       │         │
     │      Persona        │         │
     └──────┬──────────────┘         │
            │                         │
            ▼                         │
     ┌─────────────────────┐         │
     │ 4. Format Response  │         │
     │    + Sources        │         │
     │    + Confidence     │         │
     │    + Emergency flag │         │
     └──────┬──────────────┘         │
            │                         │
            ▼                         │
     ┌─────────────────────┐         │
     │ 5. Save to MongoDB  │         │
     │    queries collection│        │
     └──────┬──────────────┘         │
            │                         │
            ▼                         │
     ┌─────────────────────┐         │
     │ 6. Cache Result     │         │
     │    Redis SETEX      │         │
     │    TTL = 3600s      │         │
     └──────┬──────────────┘         │
            │                         │
            └─────────────────────────┤
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │ Return ChatResponse    │
                         │ {response, sources,    │
                         │  confidence, cached}   │
                         └────────────────────────┘
```

#### **Voice Chat Flow**
```
┌──────────┐
│  User    │
│  Audio   │
└────┬─────┘
     │
     ▼
┌──────────────────────────────────┐
│ POST /api/chat/voice             │
│ multipart: {audio, session_id}   │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ 1. Save Audio to temp/           │
│    /temp/{uuid}_{filename}       │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ 2. Whisper STT                   │
│    Audio → Text                  │
│    transcribed_query             │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ 3. Cache Check (Redis)           │
│    Key: MD5(transcribed:session) │
└────┬─────────────────────────────┘
     │
     ├─── HIT ───► Use Cached ──────┐
     │                               │
     └─── MISS                       │
          │                          │
          ▼                          │
     [Same RAG Flow as Text]        │
     (Embed → Search → LLM)         │
          │                          │
          ▼                          │
     ┌─────────────────────┐        │
     │ Cache Result        │        │
     └──────┬──────────────┘        │
            │                        │
            └────────────────────────┤
                                     │
                                     ▼
                          ┌──────────────────┐
                          │ 4. TTS Engine    │
                          │    Text → Audio  │
                          │    Save to       │
                          │    static/audio/ │
                          └────┬─────────────┘
                               │
                               ▼
                          ┌──────────────────┐
                          │ 5. Save MongoDB  │
                          └────┬─────────────┘
                               │
                               ▼
                          ┌──────────────────┐
                          │ Return Response  │
                          │ + audio_url      │
                          │ + transcribed    │
                          └──────────────────┘
```

#### **Knowledge Base Setup Flow**
```
┌─────────────────────────────────┐
│ python setup_knowledge_base.py  │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ 1. Web Scraping                 │
│    WHO, Mayo Clinic, CDC        │
│    → Extract articles           │
│    → Clean HTML                 │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ 2. Text Processing              │
│    → Chunk text                 │
│      (size=2000, overlap=200)   │
│    → Create embeddings          │
│      (384-dim vectors)          │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ 3. Pinecone Upload              │
│    → Batch upsert vectors       │
│    → Add metadata               │
│      {text, url, title, topic}  │
└────┬────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ 4. MongoDB Storage              │
│    → Save documents             │
│    → Save metadata              │
└─────────────────────────────────┘
```

---

### Database Design

#### **MongoDB Schema**

**Collection: queries**
```javascript
{
  "_id": ObjectId,              // Auto-generated
  "session_id": String,         // User session identifier
  "user_query": String,         // Original user question
  "response": String,           // Generated response
  "sources": [                  // Reference sources
    {
      "url": String,
      "title": String,
      "relevance_score": Float
    }
  ],
  "confidence": Float,          // 0.0 - 1.0
  "cached": Boolean,            // Was response cached?
  "emergency": Boolean,         // Emergency detected?
  "timestamp": ISODate,         // UTC timestamp
  "voice_enabled": Boolean      // Was this a voice query?
}

// Indexes:
// - session_id (ascending)
// - timestamp (descending)
// - cached (ascending) for analytics
```

**Collection: documents**
```javascript
{
  "_id": ObjectId,
  "url": String,                // Source URL
  "title": String,              // Article title
  "content": String,            // Full article text
  "topic": String,              // diabetes, hypertension, etc.
  "chunks": [                   // Pre-processed chunks
    {
      "text": String,
      "chunk_id": String,
      "vector_id": String       // Pinecone ID reference
    }
  ],
  "metadata": {
    "scraped_at": ISODate,
    "word_count": Int,
    "last_updated": ISODate
  },
  "status": String              // "indexed", "pending", "error"
}

// Indexes:
// - url (unique)
// - topic (ascending)
// - status (ascending)
```

#### **Redis Schema**

**Cache Keys Pattern:**
```
chat:{md5_hash}

Example:
chat:a1b2c3d4e5f6... → {
  "response": "Diabetes is...",
  "sources": [...],
  "confidence": 0.89
}

TTL: 3600 seconds (1 hour)
```

**Key Patterns:**
- `chat:{hash}` - Individual query cache
- Pattern matching for session clear: `chat:*:{session_id}`

**Data Structure:**
```json
{
  "response": "Diabetes is a chronic condition...",
  "sources": [
    {
      "url": "https://www.who.int/diabetes",
      "title": "Diabetes - WHO",
      "relevance_score": 0.92
    }
  ],
  "confidence": 0.89
}
```

#### **Pinecone Schema**

**Index Configuration:**
```yaml
Name: medical-chatbot
Dimension: 384
Metric: cosine
Pods: 1 (starter)
```

**Vector Record:**
```python
{
  "id": "doc_{uuid}_chunk_{n}",     # Unique chunk ID
  "values": [0.123, -0.456, ...],   # 384-dim embedding vector
  "metadata": {
    "text": "Diabetes symptoms include...",
    "source_url": "https://...",
    "title": "Diabetes Overview",
    "topic": "diabetes",
    "chunk_index": 0,
    "word_count": 350
  }
}
```

**Metadata Filtering:**
```python
# Filter by topic
filter = {"topic": {"$eq": "diabetes"}}

# Filter by source
filter = {"source_url": {"$eq": "https://www.who.int/..."}}
```

---

### Caching Strategy

#### **Cache Architecture**

**Technology:** Redis (in-memory key-value store)

**TTL (Time To Live):** 3600 seconds (1 hour)

**Key Generation:**
```python
def _generate_key(query: str, session_id: str) -> str:
    content = f"{query.lower().strip()}:{session_id}"
    hash_key = hashlib.md5(content.encode()).hexdigest()
    return f"chat:{hash_key}"
```

**Cache Flow:**
1. **Request arrives** → Generate cache key
2. **Check Redis** → `GET chat:{hash}`
3. **If HIT**: Return cached data (50-100ms)
4. **If MISS**: Execute RAG pipeline (2-5 seconds)
5. **Store result**: `SETEX chat:{hash} 3600 {json_data}`

**Performance Impact:**
- **Cache Hit Rate**: ~40-60% for common medical queries
- **Latency Reduction**: 20-50x faster
- **Cost Savings**: Reduces Llama 3 API calls by 40-60%

**Session-based Caching:**
- Same query + same session = cached
- Same query + different session = separate cache entries
- Reason: Personalized context may differ per session

**Cache Invalidation:**
```python
# Clear all cache for a session
await cache_manager.clear_session(session_id)

# Manual flush (admin)
redis-cli FLUSHDB
```

**Cache Statistics:**
- Monitor hit/miss rates via MongoDB analytics
- Track `cached: true/false` field in queries collection

---

## 🏗️ System Architecture Summary

**Request Flow:**
```
User → FastAPI → Cache Check → RAG Pipeline → LLM → Response
                     ↓              ↓
                   Redis         Pinecone
                                    ↓
                                 MongoDB
```

**Technology Integration:**
- **FastAPI**: Async request handling
- **Redis**: Sub-millisecond cache retrieval
- **Pinecone**: Scalable vector search
- **MongoDB**: Persistent chat history
- **Llama 3**: Open-source advanced language understanding
- **Whisper/TTS**: Natural voice interactions

## 📁 Project Structure

```
backend/
├── api/
│   └── routes/
│       ├── chat.py          # Text chat endpoint
│       ├── voice.py         # Voice chat endpoint
│       └── health.py        # Health check
├── core/
│   ├── database.py          # MongoDB & Redis clients
│   ├── cache.py             # Cache manager
│   └── persona.py           # Dr. Asha Digital Twin
├── models/
│   ├── schemas.py           # Pydantic models
│   └── database_models.py   # MongoDB models
├── repositories/
│   └── mongo_repo.py        # MongoDB operations
├── services/
│   ├── scraper.py           # Medical data scraper
│   ├── text_processor.py    # Chunking & embeddings
│   ├── vector_store.py      # Pinecone integration
│   ├── llm.py               # Gemini LLM
│   ├── rag.py               # RAG pipeline
│   └── voice.py             # Voice processing
├── scripts/
│   └── setup_knowledge_base.py
├── tests/
│   ├── test_api.py
│   ├── test_text_processor.py
│   ├── test_persona.py
│   └── test_cache.py
├── config.py
├── main.py
└── requirements.txt
```

## 🚀 Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` in the **project root** directory:

```bash
# From project root
cp .env.example .env
```

Required:
- `LLAMA_API_KEY` - Get from Groq Console (https://console.groq.com)
- `LLAMA_MODEL` - Model name (default: llama-3.3-70b-versatile)
- `PINECONE_API_KEY` - Get from Pinecone
- `PINECONE_ENVIRONMENT` - Your Pinecone environment (e.g., us-east-1)

### 3. Start Services

**MongoDB** (via Docker):
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Redis** (via Docker):
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### 4. Setup Knowledge Base

Scrape medical data and index to Pinecone:

```bash
python scripts/setup_knowledge_base.py
```

This will:
- Scrape WHO & Mayo Clinic articles
- Chunk and embed text
- Upload to Pinecone
- Save to MongoDB

### 5. Run Server

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing

```bash
# Run all tests
cd backend && pytest tests/ -v

# With coverage report
cd backend && pytest tests/ --cov=. --cov-report=html

# Run specific test file
cd backend && pytest tests/test_api.py -v
```

## 🔑 Key Features

### RAG Pipeline
1. Query embedding (sentence-transformers)
2. Vector search (Pinecone top-K)
3. Context retrieval
4. LLM generation (Llama 3 with Chain of Thought)
5. Response formatting (Dr. Asha persona)

### Digital Twin - Dr. Asha
- Empathetic medical assistant persona
- Safety constraints (no diagnosis/prescriptions)
- Emergency detection
- Source citations
- Confidence scoring

### Caching
- Redis cache with TTL
- Query hash-based keys
- Session-aware caching
- Reduces LLM costs & latency

### Voice Processing
- Whisper for accurate transcription
- TTS for natural responses
- Audio format conversion
- Temporary file cleanup

## 📊 Data Flow

```
User Query (Text/Voice)
    ↓
Cache Check (Redis)
    ↓
[MISS] → RAG Pipeline
    ↓
    1. Embed query
    2. Vector search (Pinecone)
    3. Retrieve top-K chunks
    4. Generate response (Llama 3)
    5. Format with persona
    ↓
Save to MongoDB
    ↓
Cache result
    ↓
Return response (+ audio if voice)
```

## 🔧 Development

Add new medical topics:
1. Add URLs to `services/scraper.py::MEDICAL_URLS`
2. Run `scripts/setup_knowledge_base.py`

Modify persona:
- Edit `core/persona.py::SYSTEM_PROMPT`
- Adjust `CHAIN_OF_THOUGHT_PROMPT`
