# AI Sales Assistant Chatbot

An intelligent chatbot application that uses OpenAI's GPT models with Retrieval-Augmented Generation (RAG) to provide accurate responses about a company's services, qualify incoming inquiries, and notify the sales team by email for follow up.

## Open Source

This project is open source and available under the MIT License. We welcome contributions from the community! Please see:

- [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute
- [LICENSE](LICENSE) for the full license text

## Features

- **AI-Powered Conversations**: Uses OpenAI GPT-4o-mini for natural, context-aware conversations
- **RAG (Retrieval-Augmented Generation)**: Semantic search using PostgreSQL + pgvector with optimized ivfflat indexing for accurate responses from company knowledge base
- **Intelligent Lead Qualification**:
  - Automatically collects name, email, phone, vehicle preferences, budget, and trade-in info
  - Scores leads 0-100 based on qualification criteria
  - Natural conversational flow (asks 1 question per response)
  - Triggers email notification at 60+ score with valid email
- **Email Notifications**: Mailgun integration sends instant alerts for qualified leads (60+ score)
- **FastAPI Backend**: RESTful API with CORS support and automatic documentation
- **Web Widget**: Embeddable JavaScript chat widget with session persistence
- **Session Management**: In-memory conversation history with UUID-based sessions

## Project Structure

```
ai-sales-assistant-chatbot/
├── api/                            # FastAPI server package
│   ├── __init__.py                # Package initialization
│   └── index.py                   # FastAPI server (local & Vercel)
├── chatbot.py                      # Chatbot with RAG and lead qualification
├── send_email.py                   # Email notification functionality
├── index.html                      # Web chat interface
├── vercel.json                     # Vercel deployment configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── AGENTS.md                       # AI assistant documentation
├── RAG/
│   ├── demo_content.json          # Demo car dealership content (25 entries)
│   ├── init_db.py                 # Database initialization script
│   ├── upload_to_db.py            # Load content to PostgreSQL
│   └── test_search.py             # Test RAG search functionality
└── testing/
    └── test_send_email.py         # Email functionality test
```

## Prerequisites

- Python 3.9+
- OpenAI API account
- PostgreSQL 12+ (with pgvector extension support)
- Mailgun account (for email notifications)

## Installation

### 💻 Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-sales-assistant-chatbot.git
   cd ai-sales-assistant-chatbot
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
   - `DATABASE_URL`: PostgreSQL connection string for API/production (pooler, port 6543)
   - `BATCH_DB_URL`: PostgreSQL connection string for batch scripts (session mode, port 5432)
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

2. **Configure Connection Strings**:

   You need TWO connection strings to avoid pooler issues:

   **For batch scripts** (session mode, port 5432):
   ```bash
   BATCH_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
   Use for: `init_db.py`, `upload_to_db.py`, `test_search.py`

   **For API/production** (transaction pooler, port 6543):
   ```bash
   DATABASE_URL=postgres://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   Use for: Vercel deployments, high-concurrency API servers

   > **Note**: Batch scripts will automatically fall back to `DATABASE_URL` if `BATCH_DB_URL` is not set.

3. **Initialize Database**:
   ```bash
   python RAG/init_db.py
   ```
   The script will use `BATCH_DB_URL` (or `DATABASE_URL` as fallback) to create tables and enable pgvector.

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
   createdb ai_sales_assistant_chatbot
   ```
   Or via psql:
   ```sql
   psql -U postgres
   CREATE DATABASE ai_sales_assistant_chatbot;
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
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ai_sales_assistant_chatbot
   ```

#### Option 3: Cloud PostgreSQL (Recommended for Production)

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
- Create the `company_faq` table with vector embeddings (1536-dimensional vectors)
- Create the `leads` table for qualified leads
- Create an ivfflat index for similarity search
- Set up similarity search functions

#### Load Knowledge Base

Load the demo content to populate your knowledge base:
```bash
python RAG/upload_to_db.py
```

#### Test the Setup

```bash
python RAG/test_search.py
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

Start the API server:

```bash
uvicorn api.index:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`

The same `api/index.py` file is used for both local development and Vercel deployment.

### Vercel Deployment

To deploy to Vercel, you'll need to create a `vercel.json` configuration file:

1. **Create `vercel.json` in the project root:**
   ```json
   {
     "builds": [
       {
         "src": "api/index.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "api/index.py"
       }
     ]
   }
   ```

2. **Push your code to GitHub**

3. **Import to Vercel:**
   - Go to [Vercel Dashboard](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository

4. **Configure environment variables in Vercel:**
   - Go to Project Settings > Environment Variables
   - Add all variables from your `.env` file:
     - `OPENAI_API_KEY`
     - `DATABASE_URL` (use transaction pooler URL)
     - `MAILGUN_DOMAIN`
     - `MAILGUN_API_KEY`
     - `EMAIL_FROM`
     - `EMAIL_TO`

5. **Deploy:**
   - Vercel will automatically deploy your API
   - The API will be available at `https://your-project.vercel.app`

**Note:** For Vercel deployment, make sure to use the `DATABASE_URL` with the transaction pooler (port 6543) rather than `BATCH_DB_URL`.

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### API Endpoints

#### POST /chat
Send a message to the chatbot

**Request:**
```json
{
  "message": "Do you have any SUVs in stock?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "message": "Yes! We have several SUV models available...",
  "session_id": "generated-or-provided-session-id",
  "sources": []
}
```

### Testing the Web Interface

Open `index.html` in a web browser to test the chat interface:

```bash
open index.html
```

Make sure the API server is running at `http://localhost:8080` before testing.

## Development

### Running Tests

Test the RAG search functionality:
```bash
python RAG/test_search.py
```

Test email notifications:
```bash
python testing/test_send_email.py
```

### Adding New Content

1. Edit `RAG/demo_content.json` to add/modify knowledge base entries
2. Reload the content to PostgreSQL:
   ```bash
   python RAG/upload_to_db.py
   ```

### Vector Search Performance

The chatbot uses pgvector for semantic similarity search. Performance characteristics:

- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Index Type**: ivfflat with cosine distance
- **Query Optimization**: `ivfflat.probes = 100` for maximum accuracy
- **Recommended Similarity Threshold**: 0.4+ for relevant matches

The demo dataset contains 25+ entries optimized for car dealership support.

## Deployment

The application can be deployed to various platforms:

- **Vercel** (Recommended): Serverless deployment with automatic scaling - see instructions above
- **Railway/Render**: Platform-as-a-Service with easy PostgreSQL integration
- **AWS/GCP/Azure**: Deploy as a containerized application or serverless function
- **VPS (DigitalOcean/Linode)**: Traditional server deployment with systemd

**Important:** Make sure to:
1. Set all environment variables in your deployment platform
2. Use the correct `DATABASE_URL` (pooler for production, session mode for batch scripts)
3. Enable CORS for your frontend domain in production
4. Set up SSL/HTTPS for secure connections

## Technologies Used

- **FastAPI**: Modern web framework for building APIs
- **OpenAI GPT-4o-mini**: Language model for natural conversations
- **OpenAI text-embedding-3-small**: Embedding model for semantic search (1536 dimensions)
- **PostgreSQL + pgvector 0.5.1**: Vector database for RAG functionality with cosine similarity
- **psycopg2**: PostgreSQL adapter with vector extension support
- **Beautiful Soup**: Web scraping for content extraction
- **Mailgun API**: Transactional email service for lead notifications
- **Python dotenv**: Environment variable management
- **Tailwind CSS**: Utility-first CSS framework for modern UI design

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Vector Search Returns Poor Results

**Symptoms**: Chatbot gives irrelevant answers or says "No specific information found"

**Solution**: The chatbot automatically sets `ivfflat.probes = 100` for optimal accuracy. This fixes the common issue where default settings (`probes = 1`) only check 1% of the index.

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
# For local PostgreSQL
# Install pgvector (see PostgreSQL Setup section)
psql -d ai_sales_assistant_chatbot -c "CREATE EXTENSION vector;"
```

### Empty Search Results

**Symptoms**: Database query returns 0 results

**Solution**: Check if knowledge base is loaded:
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM company_faq;"
```

If count is 0, reload the knowledge base:
```bash
python RAG/upload_to_db.py
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

This project is open source and available under the MIT License.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Demo Configuration**: This project includes demo content for Mendieta Auto Group, a fictional car dealership. Replace `RAG/demo_content.json` with your own business content to customize for your use case.
