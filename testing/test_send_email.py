#!/usr/bin/env python3
"""
Test script for Mailgun email functionality
Usage: python test_send_email.py
"""

import os
from dotenv import load_dotenv
from send_email import send_lead_notification

def test_email():
    """Test the email sending functionality with sample data"""

    # Load environment variables
    load_dotenv()

    # Check if required environment variables are set
    required_vars = ['MAILGUN_DOMAIN', 'MAILGUN_API_KEY', 'EMAIL_FROM', 'EMAIL_TO']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        return

    print("=" * 60)
    print("🧪 Testing Mailgun Email Functionality")
    print("=" * 60)
    print()

    # Display configuration (without sensitive data)
    print("Configuration:")
    print(f"✓ Mailgun Domain: {os.getenv('MAILGUN_DOMAIN')}")
    print(f"✓ API Key: {'*' * 20}{os.getenv('MAILGUN_API_KEY')[-4:]}")
    print(f"✓ From: {os.getenv('EMAIL_FROM')}")
    print(f"✓ To: {os.getenv('EMAIL_TO')}")
    print()

    # Create sample lead data
    sample_lead = {
        'company': 'Test Company Inc.',
        'email': 'test@testcompany.com',
        'budget_range': '$10,000 - $50,000',
        'timeline': '1-3 months',
        'pain_point': 'Need to improve customer engagement and automate support',
        'qualification_score': 85
    }

    print("Sample Lead Data:")
    print(f"  Company: {sample_lead['company']}")
    print(f"  Email: {sample_lead['email']}")
    print(f"  Budget: {sample_lead['budget_range']}")
    print(f"  Timeline: {sample_lead['timeline']}")
    print(f"  Pain Point: {sample_lead['pain_point']}")
    print(f"  Score: {sample_lead['qualification_score']}/100")
    print()

    # Send test email
    print("Sending test email...")
    print("-" * 60)
    send_lead_notification(sample_lead)
    print("-" * 60)
    print()

    print("✅ Test completed!")
    print()
    print("Next steps:")
    print("1. Check your inbox at:", os.getenv('EMAIL_TO'))
    print("2. If using sandbox domain, make sure recipient is authorized")
    print("3. Check Mailgun dashboard for delivery logs:")
    print("   https://app.mailgun.com/app/sending/domains")
    print()

if __name__ == "__main__":
    test_email()
