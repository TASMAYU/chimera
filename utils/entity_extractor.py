import re
from typing import Dict, List


def extract_entities(messages: List[Dict]) -> Dict:
    entities = {
        "name": None,
        "email": None,
        "company": None,
        "phone": None,
        "timeline": None
    }
    
    full_text = " ".join([msg.get("content", "") for msg in messages])
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, full_text)
    if emails:
        entities["email"] = emails[0]
    
    company_patterns = [
        r'(?:at|from|work at)\s+([A-Z][a-zA-Z\s]+(?:Corp|Inc|LLC|Ltd|Company))',
        r'([A-Z][a-z]+\s+(?:Corp|Inc|LLC|Ltd))'
    ]
    for pattern in company_patterns:
        match = re.search(pattern, full_text)
        if match:
            entities["company"] = match.group(1).strip()
            break
    
    name_patterns = [
        r'(?:my name is|i\'m|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            entities["name"] = match.group(1).strip()
            break
    
    phone_pattern = r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    phones = re.findall(phone_pattern, full_text)
    if phones:
        entities["phone"] = phones[0]
    
    if any(word in full_text.lower() for word in ["asap", "urgent", "immediately"]):
        entities["timeline"] = "urgent"
    elif any(word in full_text.lower() for word in ["next week", "next month"]):
        entities["timeline"] = "near-term"
    
    return entities
