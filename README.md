# AI Lead Scoring Chatbot

An intelligent chatbot application that uses OpenAI's GPT models with Retrieval-Augmented Generation (RAG) to provide accurate responses based on company knowledge. The chatbot includes lead qualification and email notifications.

## Features

- **AI-Powered Conversations**: Uses OpenAI GPT-4o-mini for natural, context-aware conversations
- **RAG (Retrieval-Augmented Generation)**: Semantic search using PostgreSQL + pgvector with optimized ivfflat indexing for accurate responses from company knowledge base
- **Intelligent Lead Qualification**:
  - Automatically collects email, company, budget, timeline, and pain points
  - Scores leads 0-100 based on qualification criteria
  - Natural conversational flow (asks 1 question per response)
  - Triggers email notification at 60+ score with valid email
- **Email Notifications**: Mailgun integration sends instant alerts for qualified leads (60+ score)
- **FastAPI Backend**: RESTful API with CORS support and automatic documentation
- **Web Widget**: Embeddable JavaScript chat widget with session persistence
- **Session Management**: In-memory conversation history with UUID-based sessions

## Project Structure

```
Boralio-chatbot/
├── api/                            # Vercel deployment folder
│   └── index.py                   # FastAPI server for Vercel
├── api.py                          # FastAPI server (local development)
├── chatbot.py                      # Chatbot with RAG and lead qualification
├── send_email.py                   # Email notification functionality
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── docker/                         # Docker configuration
│   ├── Dockerfile                 # API container image
│   ├── docker-compose.yml         # Multi-container orchestration
│   ├── .dockerignore              # Docker build exclusions
│   ├── .env.docker                # Docker environment template
│   └── README.md                  # Docker documentation
├── RAG/
│   ├── boralio_content.json       # Extracted company content
│   ├── extract_boralio_content.py # Web scraping script
│   ├── load_to_postgres.py        # Load content to PostgreSQL
│   ├── test_search_postgres.py    # Test RAG search functionality
│   ├── diagnose_vector_search.py  # Diagnostic tool for vector search issues
│   └── fix_vector_search_option1.py # Drop index for small datasets
└── testing/
    ├── widget.html                 # Test HTML for chat widget
    └── test_send_email.py         # Email functionality test
```

## Prerequisites

- Python 3.9+
- OpenAI API account
- PostgreSQL 12+ (with pgvector extension support)
- Mailgun account (for email notifications)

## Installation

### 🐳 Option 1: Docker (Recommended)

The easiest way to run the Boralio chatbot is using Docker. This sets up everything including PostgreSQL with pgvector and pgAdmin.

1. **Clone the repository**
   ```bash
   git clone https://github.com/christancho/boralio-chatbot.git
   cd boralio-chatbot
   ```

2. **Set up environment variables**
   ```bash
   cp docker/.env.docker .env
   ```
   Edit `.env` and add your API keys (OpenAI, Mailgun, etc.)

3. **Start the Docker stack**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **Load knowledge base**
   ```bash
   docker-compose exec api python RAG/extract_boralio_content.py
   docker-compose exec api python RAG/load_to_postgres.py
   ```

5. **Access services**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050

For detailed Docker instructions, see [docker/README.md](docker/README.md)

### 💻 Option 2: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/christancho/boralio-chatbot.git
   cd boralio-chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   - `OPENAI_API_KEY`: Your OpenAI API key from https://platform.openai.com/api-keys
   - `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:pass@host:port/dbname`)
   - `MAILGUN_DOMAIN`: Your Mailgun domain (e.g., mg.yourdomain.com)
   - `MAILGUN_API_KEY`: Your Mailgun API key
   - `EMAIL_FROM`: Sender email address (must be authorized in Mailgun)
   - `EMAIL_TO`: Recipient email for lead notifications

5. **Set up PostgreSQL** (see Configuration section below)

## Configuration

### OpenAI API Key
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create a new API key
4. Add to `.env` file

### Database Setup

#### Option 1: Supabase (Recommended for Production)

1. **Create a Supabase Project**:
   - Go to [Supabase Dashboard](https://app.supabase.com)
   - Click "New Project"
   - Note your database password

2. **Configure Connection**:
   - For development (IPv6):
     ```
     DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
     ```
   - For production/Vercel (IPv4):
     ```
     DATABASE_URL=postgres://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```

3. **Initialize Database**:
   ```bash
   python init_db.py
   ```
   The script will create all necessary tables and enable pgvector.

4. **Enable Connection Pooling**:
   - Go to Project Settings > Database
   - Find "Connection Pooling"
   - Enable pooling and note the connection string
   - Use this URL in your Vercel environment variables

#### Option 2: Local PostgreSQL Installation (Development)

1. **Install PostgreSQL** (if not already installed):
   - macOS: `brew install postgresql@15`
   - Ubuntu: `sudo apt install postgresql postgresql-contrib`
   - Windows: Download from https://www.postgresql.org/download/

2. **Start PostgreSQL service**:
   - macOS: `brew services start postgresql@15`
   - Ubuntu: `sudo systemctl start postgresql`
   - Windows: Use the pgAdmin GUI or Services manager

3. **Create database**:
   ```bash
   createdb boralio_chatbot
   ```
   Or via psql:
   ```sql
   psql -U postgres
   CREATE DATABASE boralio_chatbot;
   \q
   ```

4. **Install pgvector extension**:
   ```bash
   # macOS
   brew install pgvector

   # Ubuntu/Debian
   sudo apt install postgresql-15-pgvector

   # Or build from source
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   make
   sudo make install
   ```

5. **Update `.env` file** with your connection string:
   ```
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/boralio_chatbot
   ```

#### Option 2: Cloud PostgreSQL (Recommended for Production)

Use a managed PostgreSQL service with pgvector support:
- **Supabase** (free tier available): https://supabase.com/
- **Neon** (serverless Postgres): https://neon.tech/
- **Railway**: https://railway.app/
- **Render**: https://render.com/

Most of these services have pgvector pre-installed.

#### Initialize Database

Run the initialization script to create tables and enable pgvector:
```bash
python init_db.py
```

This will:
- Enable the pgvector extension
- Create the `blog_posts` table with vector embeddings (1536-dimensional vectors)
- Create the `leads` table for qualified leads
- Create an ivfflat index for similarity search
- Set up similarity search functions

#### Load Knowledge Base

Run the RAG setup scripts to populate your knowledge base:
```bash
python RAG/extract_boralio_content.py
python RAG/load_to_postgres.py
```

#### Test the Setup

```bash
python RAG/test_search_postgres.py
```

You should see relevant results with similarity scores above 0.4 for good matches.

#### Vector Search Optimization

The chatbot automatically configures optimal search settings:

- **`ivfflat.probes = 100`**: Set in queries for maximum recall accuracy
- **Small datasets (<1000 records)**: Index overhead is minimal, sequential scan may be faster
- **Large datasets (1000+ records)**: Consider upgrading to HNSW index for better performance

If you experience poor search quality, run the diagnostic:
```bash
python RAG/diagnose_vector_search.py
```

This will compare sequential scan vs index scan and provide recommendations.

### Mailgun Setup
1. Sign up for a free account at https://www.mailgun.com/
2. Add and verify your domain (or use the sandbox domain for testing)
3. Go to **Dashboard > Sending > Domains** and copy your domain name
4. Go to **Settings > API Keys** and copy your API key
5. Add both values to `.env` file
6. For production, verify your domain and add authorized sender addresses
7. For testing, use the sandbox domain (limited to authorized recipients)

## Running the API

### Local Development

You can run the API locally using either of these methods:

1. **Using the local development file:**
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8080 --reload
   ```

2. **Using the Vercel-compatible handler:**
   ```bash
   uvicorn api.index:app --host 0.0.0.0 --port 8080 --reload
   ```

The API will be available at `http://localhost:8080`

### Vercel Deployment

To deploy to Vercel:

1. **Push your code to GitHub**

2. **Import to Vercel:**
   - Go to [Vercel Dashboard](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Select Python framework

3. **Configure environment variables in Vercel:**
   - Go to Project Settings > Environment Variables
   - Add all variables from your `.env` file:
     - `OPENAI_API_KEY`
     - `DATABASE_URL`
     - `MAILGUN_DOMAIN`
     - `MAILGUN_API_KEY`
     - `EMAIL_FROM`
     - `EMAIL_TO`

4. **Deploy:**
   - Vercel will automatically deploy your API
   - It will use the FastAPI handler in `api/index.py`

Your API will be available at `https://your-project.vercel.app`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### POST /chat
Send a message to the chatbot

**Request:**
```json
{
  "message": "What services does Boralio offer?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "message": "Boralio offers...",
  "session_id": "generated-or-provided-session-id",
  "sources": [
    {
      "content": "Relevant source content",
      "metadata": {}
    }
  ]
}
```

### Testing the Web Widget

Open `testing/widget.html` in a web browser to test the chat widget interface.

## Development

### Running Tests

Test the RAG search functionality:
```bash
python RAG/test_search_postgres.py
```

Test email notifications:
```bash
python testing/test_send_email.py
```

Diagnose vector search performance:
```bash
python RAG/diagnose_vector_search.py
```

### Adding New Content

1. Update the content source in `RAG/extract_boralio_content.py`
2. Run the extraction script
3. Load the new content to PostgreSQL:
   ```bash
   python RAG/extract_boralio_content.py
   python RAG/load_to_postgres.py
   ```

### Vector Search Performance

The chatbot uses pgvector for semantic similarity search. Performance characteristics:

- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Index Type**: ivfflat with cosine distance
- **Query Optimization**: `ivfflat.probes = 100` for maximum accuracy
- **Recommended Similarity Threshold**: 0.4+ for relevant matches

For datasets with <1000 vectors, you may optionally drop the index for simpler configuration:
```bash
python RAG/fix_vector_search_option1.py
```

## Deployment

The application can be deployed to various platforms:

- **Heroku**: Use the included `Procfile` (if present)
- **AWS/GCP/Azure**: Deploy as a containerized application
- **Vercel/Netlify**: Deploy the API as a serverless function

Make sure to set environment variables in your deployment platform.

## Technologies Used

- **FastAPI**: Modern web framework for building APIs
- **OpenAI GPT-4o-mini**: Language model for natural conversations
- **OpenAI text-embedding-3-small**: Embedding model for semantic search (1536 dimensions)
- **PostgreSQL + pgvector 0.5.1**: Vector database for RAG functionality with cosine similarity
- **psycopg2**: PostgreSQL adapter with vector extension support
- **Beautiful Soup**: Web scraping for content extraction
- **Mailgun API**: Transactional email service for lead notifications
- **Python dotenv**: Environment variable management
- **Docker + Docker Compose**: Containerization and orchestration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Vector Search Returns Poor Results

**Symptoms**: Chatbot gives irrelevant answers or says "No specific information found"

**Solution**: The issue is likely with the ivfflat index configuration. Run diagnostics:
```bash
python RAG/diagnose_vector_search.py
```

The chatbot automatically sets `ivfflat.probes = 100` for optimal accuracy. This fixes the common issue where default settings (`probes = 1`) only check 1% of the index.

**Why this happens**: When migrating from Supabase to self-hosted PostgreSQL, the default `ivfflat.probes` setting is lower, reducing search accuracy. Supabase configures this automatically.

### Database Connection Errors

**Symptoms**: `DATABASE_URL not found` or connection refused errors

**Solution**:
1. Check `.env` file exists and contains `DATABASE_URL`
2. Verify PostgreSQL is running: `pg_isready` or `docker ps`
3. Test connection: `psql $DATABASE_URL`

### pgvector Extension Not Found

**Symptoms**: `ERROR: extension "vector" does not exist`

**Solution**:
```bash
# For Docker
docker-compose restart postgres

# For local PostgreSQL
# Install pgvector (see PostgreSQL Setup section)
psql -d boralio_chatbot -c "CREATE EXTENSION vector;"
```

### Empty Search Results

**Symptoms**: Database query returns 0 results

**Solution**: Check if knowledge base is loaded:
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM blog_posts;"
```

If count is 0, reload the knowledge base:
```bash
python RAG/extract_boralio_content.py
python RAG/load_to_postgres.py
```

### Email Notifications Not Sending

**Symptoms**: Lead qualification works but no email received

**Solution**:
1. Check Mailgun credentials in `.env` file
2. Verify sender email is authorized in Mailgun
3. For sandbox domains, add recipient to authorized list
4. Test email functionality: `python testing/test_send_email.py`
5. Check Mailgun logs at https://app.mailgun.com/app/sending/logs

## License

This project is proprietary software for Boralio.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

Built with Claude Code
