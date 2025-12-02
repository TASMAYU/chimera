from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import ConversationAgentState
from config.prompts import CONVERSATION_SYSTEM_PROMPT
from utils.intent_classifier import classify_intent, extract_confidence
from utils.entity_extractor import extract_entities
import os

def conversation_agent(
    state: ConversationAgentState,
    knowledge_base
) -> dict:
    
    user_message = state["messages"][-1]["content"]
    
    print(f"\n{'='*60}")
    print(f"[CONVERSATION] Processing: '{user_message[:50]}...'")
    print(f"[CONVERSATION] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    try:
        context_chunks = knowledge_base.search(user_message, n=3)
        context_used = len(context_chunks) > 0
        print(f"[RAG] Found {len(context_chunks)} relevant chunks")
    except Exception as e:
        print(f"[RAG] Search failed: {e}")
        context_chunks = []
        context_used = False
    
    history_messages = state["messages"][:-1]
    if history_messages:
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in history_messages
        ])
    else:
        history_str = "This is the start of the conversation."
    
    if context_chunks:
        context_str = "\n\n".join([
            f"[Context {i+1}]\n{chunk}" 
            for i, chunk in enumerate(context_chunks)
        ])
    else:
        context_str = "No relevant documents found."
    
    prompt = f"""{CONVERSATION_SYSTEM_PROMPT}

Knowledge Base Context:
{context_str}

Conversation History:
{history_str}

User's Message:
{user_message}

Your Task:
Provide a helpful response (2-4 sentences).
"""
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        response = llm.invoke(prompt)
        reply = response.content.strip()
        
        print(f"[AI] Generated reply ({len(reply)} chars)")
        
    except Exception as e:
        print(f"[AI] Failed: {e}")
        reply = "I'm having trouble right now. Please try again."
    
    intent = classify_intent(user_message)
    confidence = extract_confidence(reply)
    
    print(f"[INTENT] Detected: {intent} (confidence: {confidence})")
    
    extracted = extract_entities(state["messages"])
    
    if extracted.get("email"):
        print(f"[ENTITIES] Found email: {extracted['email']}")
    
    result = {
        "current_intent": intent,
        "confidence_score": confidence,
        "provisional_reply": reply,
        "entities": extracted,
        "retrieved_context": context_chunks,
        "context_used": context_used,
        "analytics_events": [{
            "event": "message_received",
            "session_id": state["session_id"],
            "intent": intent,
            "confidence": confidence
        }]
    }
    
    print(f"[CONVERSATION] Complete. Returning updates: {list(result.keys())}")
    print(f"{'='*60}\n")
    
    return result
