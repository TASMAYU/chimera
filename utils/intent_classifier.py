def classify_intent(message: str) -> str:
    msg_lower = message.lower()
    
    contact_keywords = [
        "email me", "send me", "contact me", "reach out",
        "call me", "phone me", "get in touch", "@"
    ]
    if any(kw in msg_lower for kw in contact_keywords):
        return "contact"
    
    demo_keywords = [
        "demo", "demonstration", "meeting", "schedule", 
        "call", "appointment", "book", "talk to",
        "see it in action", "live version", "preview"
    ]
    if any(kw in msg_lower for kw in demo_keywords):
        return "demo"
    
    pricing_keywords = [
        "price", "pricing", "cost", "how much", 
        "pay", "payment", "plan", "$", "fee",
        "investment", "budget", "rate", "charge"
    ]
    if any(kw in msg_lower for kw in pricing_keywords):
        return "pricing"
    
    return "question"


def extract_confidence(ai_response: str = None) -> float:
    return 0.85
