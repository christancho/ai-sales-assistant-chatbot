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
    "email": "What's your email address so I can send you more information?",
    "phone_number": "What's the best phone number to reach you?",
    "vehicle_type": "What type of vehicle are you interested in? (sedan, SUV, truck, EV, etc.)",
    "make_model_preference": "Do you have a specific make or model in mind?",
    "new_or_used": "Are you looking for new, used, or certified pre-owned vehicles?",
    "budget_range": "What's your budget range? (Under $20k, $20k-$35k, $35k-$50k, $50k+)",
    "trade_in": "Do you have a vehicle to trade in?",
    "financing_needed": "Are you planning to finance or pay cash?",
    "priorities": "What's most important to you? (safety, fuel economy, cargo space, towing, etc.)",
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
            FROM company_faq
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
        "phone_number": None,
        "vehicle_type": None,
        "make_model_preference": None,
        "new_or_used": None,
        "budget_range": None,
        "trade_in": None,
        "financing_needed": None,
        "priorities": None
    }

    # Extract email and phone from user messages
    for msg in conversation_history:
        if msg["role"] == "user":
            # Extract email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', msg["content"])
            if email_match:
                lead_data["email"] = email_match.group(0)

            # Extract phone number (various formats)
            phone_match = re.search(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b', msg["content"])
            if phone_match:
                lead_data["phone_number"] = phone_match.group(0)

    # Use LLM to extract other info
    extraction_prompt = f"""Analyze this conversation and extract car dealership lead information.
Return ONLY a JSON object with these fields (use null if not mentioned):
- name: person's full name
- vehicle_type: type of vehicle (sedan, SUV, truck, EV, crossover, etc.)
- make_model_preference: specific make/model mentioned (e.g., "Toyota RAV4", "Ford F-150")
- new_or_used: preference for new, used, certified pre-owned, or either
- budget_range: price range mentioned (e.g., "Under $20k", "$20k-$35k", "$35k-$50k", "$50k+")
- trade_in: whether they have a trade-in vehicle (yes/no/maybe)
- financing_needed: financing or cash purchase preference
- priorities: what's important to them (safety, fuel economy, cargo space, towing, technology, etc.)

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

    # Contact information (critical for follow-up)
    if lead_data.get("name"): score += 10
    if lead_data.get("email"): score += 20
    if lead_data.get("phone_number"): score += 20

    # Vehicle preferences (shows intent)
    if lead_data.get("vehicle_type"): score += 10
    if lead_data.get("make_model_preference"): score += 10
    if lead_data.get("new_or_used"): score += 5

    # Purchase readiness (buying signals)
    if lead_data.get("budget_range"): score += 15
    if lead_data.get("financing_needed"): score += 5
    if lead_data.get("trade_in"): score += 5

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
                session_id, name, email, phone_number, vehicle_type, make_model_preference,
                new_or_used, budget_range, trade_in, financing_needed, priorities,
                qualification_score, conversation_history
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                phone_number = EXCLUDED.phone_number,
                vehicle_type = EXCLUDED.vehicle_type,
                make_model_preference = EXCLUDED.make_model_preference,
                new_or_used = EXCLUDED.new_or_used,
                budget_range = EXCLUDED.budget_range,
                trade_in = EXCLUDED.trade_in,
                financing_needed = EXCLUDED.financing_needed,
                priorities = EXCLUDED.priorities,
                conversation_history = EXCLUDED.conversation_history,
                qualification_score = EXCLUDED.qualification_score,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *, (xmax = 0) AS inserted;
        """, (
            session_id,
            lead_data.get('name'),
            lead_data.get('email'),
            lead_data.get('phone_number'),
            lead_data.get('vehicle_type'),
            lead_data.get('make_model_preference'),
            lead_data.get('new_or_used'),
            lead_data.get('budget_range'),
            lead_data.get('trade_in'),
            lead_data.get('financing_needed'),
            lead_data.get('priorities'),
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
    system_prompt = f"""You are a helpful AI assistant for Mendieta Auto Group, a car dealership.

Your PRIMARY GOALS:
1. Answer questions about vehicles, services, inventory, and financing using the context provided
2. Qualify leads by naturally gathering: name, email, phone, vehicle preferences, budget
3. Guide qualified prospects toward scheduling a test drive or visiting the dealership

LEAD QUALIFICATION STATUS:
- Collected: {[k for k, v in lead_data.items() if v]}
- Still needed: {missing_info[:3]}  (Don't ask all at once)

QUALIFICATION APPROACH:
- Be conversational and helpful, not interrogative or pushy
- Ask 1 qualification question per response maximum
- Gather info naturally through conversation
- When you have email/phone + vehicle preference + budget → suggest scheduling a test drive or visiting the dealership
- Focus on understanding their needs: vehicle type, features, budget, trade-in, financing

Context from knowledge base:
{context}

Be friendly, enthusiastic about helping them find the right vehicle, and focused on understanding their transportation needs."""

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
    print(f"\n🤖 Mendieta Auto: {assistant_message}")
    
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
    print("💬 Mendieta Auto Group - AI Sales Assistant")
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