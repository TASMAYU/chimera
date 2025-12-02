from core.state import SchedulerAgentState
from datetime import datetime, timedelta
from typing import List, Dict

def scheduler_agent(state: SchedulerAgentState) -> dict:
    
    print(f"\n{'='*60}")
    print(f"[SCHEDULER] Finding demo slots")
    print(f"[SCHEDULER] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    try:
        slots = generate_mock_slots()
        print(f"[SCHEDULER] Found {len(slots)} slots")
    except Exception as e:
        print(f"[SCHEDULER] Failed: {e}")
        return {}
    
    formatted = format_slots_for_user(slots)
    
    urgency = state["entities"].get("timeline")
    if urgency == "urgent":
        intro = "I see you need a demo soon! Here are my earliest times:"
    else:
        intro = "I'd be happy to schedule a demo! Here are available times:"
    
    reply = f"""{intro}

{formatted}

Which time works best? Reply with the number (1, 2, 3, etc.)."""
    
    result = {
        "meeting_slots": slots,
        "provisional_reply": reply,
        "analytics_events": [{
            "event": "demo_slots_shown",
            "slots_count": len(slots)
        }]
    }
    
    print(f"[SCHEDULER] Complete")
    print(f"{'='*60}\n")
    
    return result

def generate_mock_slots() -> List[Dict]:
    
    today = datetime.now()
    slots = []
    
    for i in range(1, 6):
        date = today + timedelta(days=i)
        if date.weekday() < 5:
            slots.append({
                "id": f"slot_{i}",
                "date": date.strftime("%Y-%m-%d"),
                "time": "10:00 AM",
                "duration_minutes": 30
            })
    
    return slots[:5]

def format_slots_for_user(slots: List[Dict]) -> str:
    
    lines = []
    for i, slot in enumerate(slots, start=1):
        date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
        day_name = date_obj.strftime("%A, %B %d")
        line = f"{i}. {day_name} at {slot['time']} ({slot['duration_minutes']} min)"
        lines.append(line)
    
    return "\n".join(lines)
