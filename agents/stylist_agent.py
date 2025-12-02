from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import StylistAgentState
from config.prompts import BRAND_STYLIST_PROMPT
import os

def brand_stylist_agent(state: StylistAgentState) -> dict:
    
    print(f"\n{'='*60}")
    print(f"[STYLIST] Styling message")
    print(f"[STYLIST] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    raw_message = state["provisional_reply"]
    brand = state["brand_profile"]
    
    if len(raw_message) < 50:
        print("[STYLIST] Message too short, skipping")
        return {"sanitized_output": raw_message}
    
    tone = brand.get("tone", "professional")
    voice = brand.get("voice", "helpful")
    
    prompt = BRAND_STYLIST_PROMPT.format(
        tone=tone,
        voice=voice,
        message=raw_message
    )
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        response = llm.invoke(prompt)
        styled = response.content.strip()
        
        print(f"[STYLIST] Styled successfully")
        
    except Exception as e:
        print(f"[STYLIST] Failed: {e}, using original")
        styled = raw_message
    
    result = {
        "sanitized_output": styled
    }
    
    print(f"[STYLIST] Complete")
    print(f"{'='*60}\n")
    
    return result
