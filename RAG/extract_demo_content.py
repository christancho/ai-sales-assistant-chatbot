import requests
from bs4 import BeautifulSoup
import json

def extract_demo_content():
    """Extract demo content for the AI consulting company"""
    
    url = "https://boralio.ai"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Manual content structure (since it's a simple landing page)
    content_chunks = [
        {
            "title": "Boralio Overview",
            "content": "Boralio provides AI-powered solutions for businesses. We transform time-consuming workflows into automated systems that run 24/7, reduce errors, and scale with your business. We specialize in AI chatbots, AI agents, AI integrations, and in-house AI implementations.",
            "url": "https://boralio.ai",
            "category": "overview"
        },
        {
            "title": "AI Chatbot Development",
            "content": "We build custom AI chatbots that handle customer inquiries 24/7. Stop losing customers to slow response times. Our chatbots integrate with your existing systems and provide instant, accurate responses to common questions. Perfect for customer support, lead qualification, and FAQ automation.",
            "url": "https://boralio.ai/#chatbots",
            "category": "service"
        },
        {
            "title": "AI Agent Systems",
            "content": "Autonomous AI agents that complete complex workflows without human intervention. These agents can process data, generate reports, send communications, and handle multi-step tasks. Ideal for businesses looking to automate repetitive work that currently takes hours of staff time.",
            "url": "https://boralio.ai/#agents",
            "category": "service"
        },
        {
            "title": "AI Integrations",
            "content": "We integrate AI capabilities into your existing business tools and workflows. Whether it's adding intelligence to your CRM, automating data entry, or enhancing your analytics, we connect AI to the systems you already use. No need to replace your tech stack.",
            "url": "https://boralio.ai/#integrations",
            "category": "service"
        },
        {
            "title": "In-House AI Implementation",
            "content": "Deploy AI systems within your infrastructure. We help you build and maintain proprietary AI solutions that stay within your network. Perfect for businesses with data sensitivity requirements or those wanting full control over their AI systems.",
            "url": "https://boralio.ai/#inhouse",
            "category": "service"
        },
        {
            "title": "Technology Stack",
            "content": "We work with leading AI platforms including OpenAI, Anthropic Claude, Google Gemini, and open-source models. Our solutions integrate with popular business tools and can be deployed on-premises or in the cloud. We use modern frameworks like LangChain, CrewAI, and custom agent architectures.",
            "url": "https://boralio.ai/#platforms",
            "category": "technology"
        },
        {
            "title": "Location and Contact",
            "content": "Boralio is based in Montreal, Canada. We work remotely with clients across North America. Available for coffee meetings anywhere in Montreal. Contact us to discuss your AI automation needs and get a custom solution designed for your business.",
            "url": "https://boralio.ai/#contact",
            "category": "contact"
        },
        {
            "title": "Ideal Clients",
            "content": "We work best with businesses that have repetitive workflows consuming staff time, slow customer response times affecting revenue, or manual processes prone to errors. If you're spending hours on tasks that could be automated, or losing customers due to delayed responses, Boralio can help.",
            "url": "https://boralio.ai/#ideal-clients",
            "category": "sales"
        },
        {
            "title": "Getting Started",
            "content": "Getting started with Boralio is simple: 1) Book a discovery call to discuss your needs, 2) We analyze your workflows and propose AI solutions, 3) Build a proof-of-concept to demonstrate value, 4) Deploy and scale the solution across your business. Most projects show ROI within 90 days.",
            "url": "https://boralio.ai/#process",
            "category": "sales"
        }
    ]
    
    return content_chunks

if __name__ == "__main__":
    # Use the local extractor and write to demo_content.json so other scripts
    # (e.g. RAG/upload_to_db.py) can find the file.
    content = extract_demo_content()

    # Save to JSON for review
    with open('demo_content.json', 'w') as f:
        json.dump(content, f, indent=2)

    print(f"✅ Extracted {len(content)} content chunks")
    print("📄 Saved to demo_content.json")