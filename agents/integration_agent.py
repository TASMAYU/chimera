from core.state import IntegrationAgentState


def integration_agent(state: IntegrationAgentState) -> dict:
    
    print(f"\n{'='*60}")
    print(f"[INTEGRATION] Processing external systems")
    print(f"[INTEGRATION] State access: {list(state.keys())}")
    print(f"{'='*60}")
    
    
    crm_payload = state.get("crm_payload")
    meeting_slots = state.get("meeting_slots")
    
    events = []
    
    
    if crm_payload:
        print(f"[INTEGRATION] Pushing to CRM:")
        print(f"  Email: {crm_payload.get('email')}")
        print(f"  Company: {crm_payload.get('company')}")
        print(f"  Score: {crm_payload.get('lead_score')}/100")
        
        success = push_to_crm_mock(crm_payload)
        
        if success:
            events.append({
                "event": "crm_sync_success",
                "email": crm_payload.get("email")
            })
        else:
            events.append({
                "event": "crm_sync_failed"
            })
    
    
    if meeting_slots:
        print(f"[INTEGRATION] Would book calendar (Phase 3)")
    
    
    print(f"[INTEGRATION] Complete")
    print(f"{'='*60}\n")
    
    return {
        "analytics_events": events
    }


def push_to_crm_mock(payload: dict) -> bool:
    
    print("\n[MOCK CRM] Would send to HubSpot:")
    print(f"  POST /crm/v3/objects/contacts")
    print(f"  Body: {payload}\n")
    
    return True
