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

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
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
            FROM blog_posts
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
    # Test queries
    test_queries = [
        "How can you help automate customer support?",
        "What AI platforms do you work with?",
        "Do you work with clients outside Montreal?",
        "How much does an AI chatbot cost?",
    ]

    for query in test_queries:
        search(query)
        print("-" * 80)
