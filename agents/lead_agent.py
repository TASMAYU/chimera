from core.state import LeadAgentState
from typing import Dict

def lead_qualification_agent(state: LeadAgentState) -> dict:
    
    entities = state["entities"]
    messages = state["messages"]
    
    print(f"\n{'='*60}")
    print(f"[LEAD QUAL] Starting")
    print(f"[LEAD QUAL] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    if not entities.get("email"):
        print("[LEAD QUAL] No email found")
        return {}
    
    bant_score = calculate_bant_score(entities, messages)
    
    if bant_score >= 75:
        qualification = "hot"
    elif bant_score >= 50:
        qualification = "warm"
    else:
        qualification = "cold"
    
    print(f"[LEAD QUAL] Score: {bant_score}/100 ({qualification.upper()})")
    
    crm_payload = {
        "email": entities.get("email"),
        "name": entities.get("name", "Unknown"),
        "company": entities.get("company"),
        "phone": entities.get("phone"),
        "source": "chimera_chatbot",
        "lead_score": bant_score,
        "qualification": qualification
    }
    
    result = {
        "lead_data": {
            "score": bant_score,
            "qualification": qualification
        },
        "lead_status": qualification,
        "crm_payload": crm_payload,
        "analytics_events": [{
            "event": "lead_qualified",
            "qualification": qualification,
            "score": bant_score
        }]
    }
    
    print(f"[LEAD QUAL] Complete")
    print(f"{'='*60}\n")
    
    return result

def calculate_bant_score(entities: Dict, messages: list) -> int:
    
    conversation = " ".join([m.get("content", "") for m in messages]).lower()
    
    score = 0
    
    if any(kw in conversation for kw in ["budget", "invest", "spend"]):
        score += 20
    
    if entities.get("company"):
        score += 10
    if any(kw in conversation for kw in ["i need", "we need"]):
        score += 15
    
    if any(kw in conversation for kw in ["problem", "issue", "help"]):
        score += 20
    
    timeline = entities.get("timeline")
    if timeline == "urgent":
        score += 25
    elif timeline == "near-term":
        score += 15
    
    if entities.get("email"):
        score += 15
    if entities.get("phone"):
        score += 10
    
    return min(score, 100)
