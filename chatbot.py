import os
import json
import re
from datetime import datetime
from openai import OpenAI
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from send_email import send_lead_notification
from pgvector.psycopg2 import register_vector

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_db_connection():
    """Get PostgreSQL database connection"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    conn = psycopg2.connect(database_url)
    register_vector(conn)
    return conn

# Lead qualification criteria
QUALIFICATION_QUESTIONS = {
    "name": "What's your name?",
    "email": "To send you more information, what's your email address?",
    "company": "What company are you with?",
    "company_size": "How large is your team? (1-10, 11-50, 51-200, 200+)",
    "budget_range": "What's your budget range for AI automation? ($5k-15k, $15k-50k, $50k+)",
    "timeline": "When are you looking to implement? (This month, Next quarter, Exploring)",
    "pain_point": "What's the biggest workflow challenge you're trying to solve?",
}

def get_relevant_context(question, threshold=0.45, limit=3):
    """Retrieve relevant content from vector DB"""
    try:
        response = openai_client.embeddings.create(
            input=question,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Set ivfflat.probes for better recall (match lists parameter from index)
        # This fixes the accuracy issue - default probes=1 checks only 1 of 100 lists
        cur.execute("SET ivfflat.probes = 100;")

        # Direct query with low threshold
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
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """, (query_embedding, query_embedding, limit))

        results = cur.fetchall()

        # Debug: show what we got
        if results:
            print(f"[DEBUG] Retrieved {len(results)} results, top similarity: {results[0]['similarity']:.4f}")
        else:
            print(f"[DEBUG] Query returned 0 results - checking database connectivity")

        cur.close()
        conn.close()

        return results
    except Exception as e:
        print(f"❌ Error retrieving context: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_lead_info(conversation_history):
    """Extract lead information from conversation"""
    lead_data = {
        "name": None,
        "email": None,
        "company": None,
        "company_size": None,
        "budget_range": None,
        "timeline": None,
        "pain_point": None,
        "is_decision_maker": None
    }

    # Extract email
    for msg in conversation_history:
        if msg["role"] == "user":
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', msg["content"])
            if email_match:
                lead_data["email"] = email_match.group(0)

    # Use LLM to extract other info
    extraction_prompt = f"""Analyze this conversation and extract lead qualification information.
Return ONLY a JSON object with these fields (use null if not mentioned):
- name: person's full name
- company: company name
- company_size: team size category
- budget_range: budget mentioned
- timeline: implementation timeline
- pain_point: main problem they're trying to solve
- is_decision_maker: true/false if they mentioned being decision maker

Conversation:
{json.dumps(conversation_history, indent=2)}

JSON only, no explanation:"""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        extracted = json.loads(response.choices[0].message.content)
        lead_data.update({k: v for k, v in extracted.items() if v})
    except:
        pass
    
    return lead_data

def calculate_qualification_score(lead_data):
    """Calculate lead qualification score 0-100"""
    score = 0
    
    if lead_data.get("email"): score += 20
    if lead_data.get("company"): score += 10
    if lead_data.get("budget_range"): score += 25
    if lead_data.get("timeline"): score += 15
    if lead_data.get("pain_point"): score += 20
    if lead_data.get("is_decision_maker"): score += 10
    
    return score

def save_lead(lead_data, conversation_history, session_id):
    """Save qualified lead to database (only once per session)"""
    try:
        score = calculate_qualification_score(lead_data)

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Use INSERT ... ON CONFLICT to prevent duplicates per session
        # If session_id already exists, update the conversation history
        cur.execute("""
            INSERT INTO leads (
                session_id, name, email, company, company_size, budget_range, timeline,
                pain_point, is_decision_maker, qualification_score, conversation_history
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                company = EXCLUDED.company,
                company_size = EXCLUDED.company_size,
                budget_range = EXCLUDED.budget_range,
                timeline = EXCLUDED.timeline,
                pain_point = EXCLUDED.pain_point,
                is_decision_maker = EXCLUDED.is_decision_maker,
                conversation_history = EXCLUDED.conversation_history,
                qualification_score = EXCLUDED.qualification_score,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *, (xmax = 0) AS inserted;
        """, (
            session_id,
            lead_data.get('name'),
            lead_data.get('email'),
            lead_data.get('company'),
            lead_data.get('company_size'),
            lead_data.get('budget_range'),
            lead_data.get('timeline'),
            lead_data.get('pain_point'),
            lead_data.get('is_decision_maker'),
            score,
            json.dumps(conversation_history)
        ))

        result = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        return dict(result) if result else None
    except Exception as e:
        print(f"Error saving lead: {e}")
        import traceback
        traceback.print_exc()
        return None

def chat(user_message, conversation_history=None, session_id=None):
    """Enhanced chat with lead qualification"""
    
    if conversation_history is None:
        conversation_history = []
    
    print(f"\n🧑 User: {user_message}")
    
    # Get relevant context
    context_docs = get_relevant_context(user_message)
    
    if context_docs:
        context = "\n\n".join([
            f"Source: {doc['title']}\n{doc['content']}"
            for doc in context_docs
        ])
        print(f"📚 Found {len(context_docs)} relevant sources")
    else:
        context = "No specific information found."
        print("⚠️  No relevant sources found")
    
    # Extract current lead info
    lead_data = extract_lead_info(conversation_history + [{"role": "user", "content": user_message}])
    missing_info = [k for k, v in lead_data.items() if v is None]
    
    # Build system prompt with qualification guidance
    system_prompt = f"""You are a helpful AI assistant for an AI consulting company.

Your PRIMARY GOALS:
1. Answer questions about Boralio's services using the context provided
2. Qualify leads by naturally gathering: email, company, budget, timeline, pain points
3. Guide qualified prospects toward booking a discovery call

LEAD QUALIFICATION STATUS:
- Collected: {[k for k, v in lead_data.items() if v]}
- Still needed: {missing_info[:3]}  (Don't ask all at once)

QUALIFICATION APPROACH:
- Be conversational and helpful, not interrogative
- Ask 1 qualification question per response maximum
- Gather info naturally through conversation
- When you have email + budget + timeline → offer to book discovery call

Context from knowledge base:
{context}

Be friendly, consultative, and focused on understanding their needs."""

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    # Get response
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    assistant_message = response.choices[0].message.content
    print(f"\n🤖 Boralio AI: {assistant_message}")
    
    # Update conversation history
    conversation_history.append({
        "role": "user", 
        "content": user_message,
        "timestamp": datetime.utcnow().isoformat()
    })
    conversation_history.append({
        "role": "assistant", 
        "content": assistant_message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Save conversation (optional - implement if needed)
    # Note: Session persistence can be added to PostgreSQL if required
    
    # Check if lead is qualified
    score = calculate_qualification_score(lead_data)
    if score >= 60 and lead_data.get("email"):
        print(f"\n🎯 QUALIFIED LEAD! Score: {score}/100")
        saved_lead = save_lead(lead_data, conversation_history, session_id)
        if saved_lead:
            # Only send email if this is a NEW lead (inserted=True)
            # The 'inserted' field tells us if it was an INSERT or UPDATE
            if saved_lead.get('inserted', False):
                print(f"✅ New lead saved to database with ID: {saved_lead['id']}")
                send_lead_notification(saved_lead)
            else:
                print(f"✅ Lead {saved_lead['id']} updated (no duplicate email sent)") 
    
    # Show sources
    if context_docs:
        print("\n📎 Sources:")
        for doc in context_docs:
            print(f"  • {doc['title']}")
    
    return assistant_message, conversation_history

def interactive_chat():
    """Interactive chat session"""
    import uuid
    
    session_id = str(uuid.uuid4())
    print("=" * 80)
    print("💬 Boralio AI Chatbot - Lead Qualification Mode")
    print(f"📝 Session ID: {session_id}")
    print("=" * 80)
    print("Type 'quit' to exit\n")
    
    conversation_history = []
    
    while True:
        user_input = input("\n🧑 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n👋 Thanks for chatting!")
            break
        
        if not user_input:
            continue
        
        _, conversation_history = chat(user_input, conversation_history, session_id)
        print("\n" + "-" * 80)

if __name__ == "__main__":
    interactive_chat()