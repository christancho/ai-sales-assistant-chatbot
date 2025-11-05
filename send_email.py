import os
import json
import requests

def send_lead_notification(lead_data):
    """Send email when lead is qualified using Mailgun API"""

    # Mailgun configuration
    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    mailgun_api_key = os.getenv("MAILGUN_API_KEY")
    sender = os.getenv("EMAIL_FROM")  # Your sender email (e.g., noreply@yourdomain.com)
    recipient = os.getenv("EMAIL_TO", "christianmendieta@gmail.com")  # Recipient email

    # Validate configuration
    if not mailgun_domain or not mailgun_api_key:
        print("❌ Mailgun configuration missing. Please set MAILGUN_DOMAIN and MAILGUN_API_KEY")
        return

    lead_name = lead_data.get('name', 'Unknown')
    subject = f"🎯 New Qualified Lead: {lead_name}"

    # Format conversation history
    conversation_transcript = ""
    conversation_history = lead_data.get('conversation_history')

    if conversation_history:
        # Parse if it's a JSON string
        if isinstance(conversation_history, str):
            try:
                conversation_history = json.loads(conversation_history)
            except:
                pass

        # Format the conversation
        if isinstance(conversation_history, list):
            conversation_transcript = "\n" + "=" * 60 + "\nCONVERSATION TRANSCRIPT\n" + "=" * 60 + "\n\n"
            for msg in conversation_history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')

                if role == 'user':
                    conversation_transcript += f"👤 USER ({timestamp}):\n{content}\n\n"
                elif role == 'assistant':
                    conversation_transcript += f"🤖 ASSISTANT ({timestamp}):\n{content}\n\n"

            conversation_transcript += "=" * 60 + "\n"

    body = f"""
New qualified lead from Boralio chatbot!

LEAD INFORMATION
================
Name: {lead_data.get('name')}
Company: {lead_data.get('company')}
Email: {lead_data.get('email')}
Budget: {lead_data.get('budget_range')}
Timeline: {lead_data.get('timeline')}
Pain Point: {lead_data.get('pain_point')}
Score: {lead_data.get('qualification_score')}/100
{conversation_transcript}
    """

    # Mailgun API endpoint
    url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

    # Prepare the request
    data = {
        "from": f"AI Lead Chatbot <{sender}>",
        "to": [recipient],
        "subject": subject,
        "text": body
    }

    try:
        response = requests.post(
            url,
            auth=("api", mailgun_api_key),
            data=data
        )

        if response.status_code == 200:
            print("✅ Email notification sent successfully!")
            print(f"📧 Message ID: {response.json().get('id')}")
        else:
            print(f"❌ Email failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Email failed: {e}")