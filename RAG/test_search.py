import os
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search(question):
    """Search Boralio content for relevant information"""

    # Use BATCH_DB_URL for batch operations (session mode, port 5432)
    # Falls back to DATABASE_URL if BATCH_DB_URL is not set
    database_url = os.getenv("BATCH_DB_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ BATCH_DB_URL or DATABASE_URL not found in environment variables")
        return []

    print(f"\n🔍 Question: {question}\n")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        register_vector(conn)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Set ivfflat.probes for better recall
        cur.execute("SET ivfflat.probes = 100;")

        # Generate query embedding
        response = openai_client.embeddings.create(
            input=question,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        # Direct similarity search
        cur.execute("""
            SELECT
                id,
                title,
                content,
                excerpt,
                url,
                metadata,
                (1 - (embedding <=> %s::vector))::float as similarity
            FROM company_faq
            ORDER BY embedding <=> %s::vector
            LIMIT 3;
        """, (query_embedding, query_embedding))

        results = cur.fetchall()

        print("📊 Top Results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   Similarity: {result['similarity']:.3f}")
            print(f"   Content: {result['content'][:150]}...")
            print(f"   URL: {result['url']}\n")

        # Close connection
        cur.close()
        conn.close()

        return results

    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

if __name__ == "__main__":
    # Test queries (dealer & vehicle-focused to match demo_content.json)
    test_queries = [
        "Where can I schedule a test drive?",
        "Do you have a Toyota RAV4 in stock?",
        "Tell me about Ford F-Series towing capacity",
        "How do I get financing for a new car?",
        "What warranty and protection plans do you offer?",
        "Do you offer certified pre-owned vehicles and inspections?",
        "What are the current special offers and incentives?",
        "How can I order OEM parts and accessories?",
        "Which electric vehicle models and charging support do you provide?",
        "What is the trade-in appraisal process and how do I get a quote?",
    ]

    for query in test_queries:
        search(query)
        print("-" * 80)
