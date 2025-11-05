import os
import json
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text):
    """Generate embedding using OpenAI"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def load_content():
    """Load Boralio content into PostgreSQL"""

    # Use BATCH_DB_URL for batch operations (session mode, port 5432)
    # Falls back to DATABASE_URL if BATCH_DB_URL is not set
    database_url = os.getenv("BATCH_DB_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ BATCH_DB_URL or DATABASE_URL not found in environment variables")
        return

    print(f"🔗 Using: {'BATCH_DB_URL' if os.getenv('BATCH_DB_URL') else 'DATABASE_URL'}")

    # Load content
    with open('demo_content.json', 'r') as f:
        content_chunks = json.load(f)

    print(f"📥 Loading {len(content_chunks)} content chunks...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        register_vector(conn)
        cur = conn.cursor()

        # Clear existing data (optional - comment out if you want to keep old data)
        try:
            cur.execute("DELETE FROM company_faq WHERE id > 0;")
            conn.commit()
            print("🗑️  Cleared existing data\n")
        except Exception as e:
            print(f"⚠️  Could not clear data: {e}\n")
            conn.rollback()

        for i, chunk in enumerate(content_chunks, 1):
            print(f"  Processing {i}/{len(content_chunks)}: {chunk['title']}")

            try:
                # Generate embedding
                embedding_text = f"{chunk['title']}\n\n{chunk['content']}"
                embedding = generate_embedding(embedding_text)

                # Prepare data
                cur.execute("""
                    INSERT INTO company_faq (title, content, excerpt, url, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    chunk['title'],
                    chunk['content'],
                    chunk['content'][:200],  # First 200 chars as excerpt
                    chunk['url'],
                    embedding,
                    json.dumps({"category": chunk['category']})
                ))

                inserted_id = cur.fetchone()[0]
                conn.commit()
                print(f"    ✅ Inserted with ID: {inserted_id}")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                conn.rollback()
                continue

        print("\n🎉 Loading complete!")

        # Verify count
        cur.execute("SELECT COUNT(*) FROM company_faq;")
        count = cur.fetchone()[0]
        print(f"📊 Total records in database: {count}")

        # Close connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    load_content()
