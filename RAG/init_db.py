#!/usr/bin/env python3
"""
Initialize PostgreSQL database with pgvector extension for AI lead scoring chatbot
Usage: python init_db.py
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Initialize database with pgvector extension and create tables"""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        return

    print("🔧 Initializing PostgreSQL database...")
    print()

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Enable pgvector extension
        print("📦 Enabling pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension enabled")
        print()

        # Create blog_posts table with vector column
        print("📋 Creating blog_posts table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                url TEXT,
                embedding vector(1536),  -- OpenAI text-embedding-3-small dimensions
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ blog_posts table created")
        print()

        # Create index for vector similarity search
        print("🔍 Creating vector similarity index...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS blog_posts_embedding_idx
            ON blog_posts
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        print("✅ Vector index created")
        print()

        # Create similarity search function
        print("⚙️  Creating similarity search function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION match_blog_posts(
                query_embedding vector(1536),
                match_threshold float DEFAULT 0.5,
                match_count int DEFAULT 3
            )
            RETURNS TABLE (
                id int,
                title text,
                content text,
                excerpt text,
                url text,
                metadata jsonb,
                similarity float
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    blog_posts.id,
                    blog_posts.title,
                    blog_posts.content,
                    blog_posts.excerpt,
                    blog_posts.url,
                    blog_posts.metadata,
                    1 - (blog_posts.embedding <=> query_embedding) as similarity
                FROM blog_posts
                WHERE 1 - (blog_posts.embedding <=> query_embedding) > match_threshold
                ORDER BY blog_posts.embedding <=> query_embedding
                LIMIT match_count;
            END;
            $$;
        """)
        print("✅ Similarity search function created")
        print()

        # Create leads table for tracking qualified leads
        print("📊 Creating leads table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                company TEXT,
                company_size TEXT,
                budget_range TEXT,
                timeline TEXT,
                pain_point TEXT,
                is_decision_maker BOOLEAN,
                qualification_score INT,
                conversation_history JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ leads table created")
        print()

        # Check if there's data
        cur.execute("SELECT COUNT(*) FROM blog_posts;")
        count = cur.fetchone()[0]
        print(f"📈 Current blog_posts count: {count}")
        print()

        # Close connection
        cur.close()
        conn.close()

        print("✅ Database initialization complete!")
        print()
        print("Next steps:")
        print("1. Run: python RAG/extract_boralio_content.py")
        print("2. Run: python RAG/load_to_postgres.py")
        print("3. Run: python RAG/test_search.py")

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print()
        print("Make sure:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL is correct in .env")
        print("3. You have permissions to create extensions")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_database()
