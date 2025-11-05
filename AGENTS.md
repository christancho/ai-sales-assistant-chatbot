# AGENTS.MD - AI Assistant Context

AI-powered lead qualification chatbot for **Mendieta Auto Group** (car dealership) using RAG architecture.

## Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| **LLM** | OpenAI GPT-4o-mini | Conversation & extraction |
| **Embeddings** | text-embedding-3-small | 1536 dimensions |
| **Vector DB** | PostgreSQL + pgvector 0.5.1 | Cosine similarity |
| **API** | FastAPI | CORS-enabled, Vercel-compatible |
| **Email** | Mailgun API | Lead notifications |
| **Index** | ivfflat | 100 lists, **probes=100** (critical) |
| **Sessions** | In-memory dict | Use Redis for production |

## Core Files

```
chatbot.py              # Main logic: RAG + lead qualification + scoring
api.py                  # FastAPI server (local)
api/index.py            # Vercel serverless handler
send_email.py           # Mailgun notifications
RAG/demo_content.json   # Knowledge base (25 car/dealer entries)
RAG/init_db.py          # PostgreSQL schema
RAG/upload_to_db.py     # Load content to DB
```

## Database Schema

### `company_faq` - RAG Knowledge Base
```sql
CREATE TABLE company_faq (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX company_faq_embedding_idx ON company_faq
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### `leads` - Qualified Leads
```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    name TEXT,
    email TEXT,
    phone_number TEXT,
    vehicle_type TEXT,
    make_model_preference TEXT,
    new_or_used TEXT,
    budget_range TEXT,
    trade_in TEXT,
    financing_needed TEXT,
    priorities TEXT,
    qualification_score INT,
    conversation_history JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Lead Qualification Scoring

**Total: 100 points**

Contact Info (50):
- Email: 20
- Phone: 20
- Name: 10

Vehicle Preferences (25):
- Type (SUV/truck/sedan): 10
- Make/Model: 10
- New/Used: 5

Purchase Readiness (25):
- Budget: 15
- Financing: 5
- Trade-in: 5

**Trigger**: Score ≥ 60 + valid email → saves lead + sends email notification

## Key Functions (chatbot.py)

**`get_relevant_context(question, limit=3)`** (lines 39-83)
- Generates embedding with OpenAI
- **CRITICAL**: Sets `ivfflat.probes = 100` for accuracy
- Returns top 3 matches from vector DB

**`extract_lead_info(conversation_history)`** (lines 85-142)
- Regex: extracts email + phone
- LLM: extracts vehicle preferences, budget, priorities

**`calculate_qualification_score(lead_data)`** (lines 144-163)
- Returns 0-100 score based on collected fields

**`save_lead(lead_data, conversation_history, session_id)`** (lines 165-220)
- Upserts to `leads` table using `ON CONFLICT (session_id)`
- Returns `inserted` flag (true = new lead, false = update)

**`chat(user_message, conversation_history, session_id)`** (lines 229-303)
- Retrieves RAG context
- Builds system prompt with qualification status
- Generates response (GPT-4o-mini)
- Asks max 1 qualification question per response
- Triggers email when score ≥ 60

## Qualification Questions

```python
QUALIFICATION_QUESTIONS = {
    "name": "What's your name?",
    "email": "What's your email address so I can send you more information?",
    "phone_number": "What's the best phone number to reach you?",
    "vehicle_type": "What type of vehicle are you interested in?",
    "make_model_preference": "Do you have a specific make or model in mind?",
    "new_or_used": "Are you looking for new, used, or certified pre-owned?",
    "budget_range": "What's your budget range?",
    "trade_in": "Do you have a vehicle to trade in?",
    "financing_needed": "Are you planning to finance or pay cash?",
    "priorities": "What's most important to you?",
}
```

## System Prompt Strategy

1. **Role**: AI assistant for Mendieta Auto Group
2. **Goals**: Answer questions, qualify leads, guide to test drive
3. **Approach**: Conversational, helpful, max 1 question per response
4. **Context**: RAG results injected from vehicle facts + services
5. **Tone**: Friendly, enthusiastic, focused on finding right vehicle

## Environment Variables

```bash
OPENAI_API_KEY=sk-...

# For API/production (transaction pooler, port 6543)
DATABASE_URL=postgres://postgres.[REF]:[PASS]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# For batch scripts (session mode, port 5432) - avoids pooler issues
BATCH_DB_URL=postgresql://postgres:[PASS]@db.[REF].supabase.co:5432/postgres

MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_API_KEY=...
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=sales@yourdomain.com
```

**Database Connection Strategy:**
- `DATABASE_URL`: API/chatbot uses transaction pooler (port 6543)
- `BATCH_DB_URL`: Scripts use session mode (port 5432) - prevents "duplicate SASL authentication" errors

## Critical Configuration

### Vector Search Accuracy

```python
# CRITICAL: Set probes=100 for accuracy
cur.execute("SET ivfflat.probes = 100;")
```

**Why**: Default `probes=1` checks only 1% of index. Setting `probes=100` checks all 100 lists for maximum recall. Essential for datasets <1000 vectors.

### Email Deduplication

- Uses `session_id` as unique key
- `ON CONFLICT (session_id) DO UPDATE` prevents duplicates
- Email sent only when `inserted=true` (new lead)

## API Endpoints

**POST /chat**
- Request: `{message: str, session_id?: str}`
- Response: `{message: str, session_id: str, sources: []}`

**GET /health**
- Health check

## Quick Start

```bash
# Setup
pip install -r requirements.txt
python RAG/init_db.py
python RAG/upload_to_db.py

# Run
uvicorn api:app --reload          # API server
python chatbot.py                 # Interactive CLI
```

## Important Notes for AI Assistants

1. **DO NOT remove `ivfflat.probes = 100`** - critical for search accuracy
2. **Score threshold is 60** - well-tested
3. **Max 1 question per response** - natural conversation flow
4. **Session deduplication by design** - prevents spam emails
5. **demo_content.json is source of truth** - reload with `upload_to_db.py` after changes
6. **In-memory sessions are temporary** - migrate to Redis for production

---

**Domain**: Car Dealership Support & Lead Qualification
**Language**: Python 3.9+
**Dependencies**: FastAPI, OpenAI SDK, psycopg2, pgvector, requests
