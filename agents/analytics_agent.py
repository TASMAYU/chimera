from core.state import AnalyticsAgentState
from datetime import datetime

def analytics_agent(state: AnalyticsAgentState) -> dict:
    print(f"\n{'='*60}")
    print(f"[ANALYTICS] Logging conversation")
    print(f"[ANALYTICS] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    session_id = state["session_id"]
    events = state.get("analytics_events", [])
    
    print(f"[ANALYTICS] Events ({len(events)}):")
    for event in events:
        event_type = event.get("event", "unknown")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{timestamp}] {event_type}")
    
    metrics = {
        "session_id": session_id,
        "total_events": len(events),
        "event_types": list(set(e.get("event") for e in events)),
        "logged_at": datetime.now().isoformat()
    }
    
    print(f"\n[ANALYTICS] Summary:")
    print(f"  Session: {session_id}")
    print(f"  Total events: {metrics['total_events']}")
    print(f"  Event types: {', '.join(metrics['event_types'])}")
    
    print(f"[ANALYTICS] Complete")
    print(f"{'='*60}\n")
    
    return {
        "conversation_metrics": metrics
    }
