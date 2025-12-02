from core.state import ChimeraFullState
from core.state_filter import StateFilter
from typing import Dict, List
import copy

def supervisor_agent(full_state: ChimeraFullState) -> ChimeraFullState:
    phase = full_state.get("supervisor_phase", "initial_analysis")
    iteration = full_state.get("iteration_count", 0)
    
    print(f"\n{'='*60}")
    print(f"[SUPERVISOR] Pass #{iteration + 1} - Phase: {phase}")
    print(f"[SUPERVISOR] Full state access: YES")
    print(f"[SUPERVISOR] Fields: {list(full_state.keys())}")
    print(f"{'='*60}")
    
    if iteration >= 10:
        print("[SUPERVISOR] Max iterations reached. Ending.")
        full_state["next_action"] = "analytics"
        return full_state
    
    if phase == "initial_analysis":
        routing = phase_1_initial_analysis(full_state)
    elif phase == "result_collection":
        routing = phase_2_result_collection(full_state)
    elif phase == "post_processing":
        routing = phase_3_post_processing(full_state)
    else:
        routing = {"agents": [], "mode": "done"}
    
    agents_to_call = routing.get("agents", [])
    mode = routing.get("mode", "sequential")
    next_phase = routing.get("next_phase", "finalization")
    
    print(f"[SUPERVISOR] Decision:")
    print(f"  Agents: {', '.join(agents_to_call) if agents_to_call else 'none'}")
    print(f"  Mode: {mode}")
    print(f"  Next phase: {next_phase}")
    
    if agents_to_call:
        if mode == "parallel":
            full_state = call_agents_parallel_filtered(full_state, agents_to_call)
        else:
            for agent_name in agents_to_call:
                full_state = call_agent_filtered(full_state, agent_name)
    
    full_state["supervisor_phase"] = next_phase
    full_state["previous_agent"] = "supervisor"
    full_state["iteration_count"] += 1
    
    if mode == "done":
        full_state["next_action"] = "analytics"
    else:
        full_state["next_action"] = "supervisor"
    
    print(f"[SUPERVISOR] Next: {full_state['next_action']}")
    print(f"{'='*60}\n")
    
    return full_state

def call_agent_filtered(
    full_state: ChimeraFullState,
    agent_name: str
) -> ChimeraFullState:
    
    print(f"\n[SUPERVISOR] Calling {agent_name} with filtered state")
    
    from agents.lead_agent import lead_qualification_agent
    from agents.scheduler_agent import scheduler_agent
    from agents.stylist_agent import brand_stylist_agent
    from agents.compliance_agent import compliance_agent
    from agents.integration_agent import integration_agent
    from agents.analytics_agent import analytics_agent
    
    if agent_name == "lead_agent":
        filtered_state = StateFilter.for_lead_agent(full_state)
        agent_func = lead_qualification_agent
    elif agent_name == "scheduler_agent":
        filtered_state = StateFilter.for_scheduler_agent(full_state)
        agent_func = scheduler_agent
    elif agent_name == "stylist_agent":
        filtered_state = StateFilter.for_stylist_agent(full_state)
        agent_func = brand_stylist_agent
    elif agent_name == "compliance_agent":
        filtered_state = StateFilter.for_compliance_agent(full_state)
        agent_func = compliance_agent
    elif agent_name == "integration_agent":
        filtered_state = StateFilter.for_integration_agent(full_state)
        agent_func = integration_agent
    elif agent_name == "analytics_agent":
        filtered_state = StateFilter.for_analytics_agent(full_state)
        agent_func = analytics_agent
    else:
        print(f"[SUPERVISOR] Unknown agent: {agent_name}")
        return full_state
    
    try:
        agent_result = agent_func(filtered_state)
        print(f"[SUPERVISOR] {agent_name} returned: {list(agent_result.keys())}")
    except Exception as e:
        print(f"[SUPERVISOR] {agent_name} failed: {e}")
        return full_state
    
    full_state = merge_agent_result(full_state, agent_name, agent_result)
    
    print(f"[SUPERVISOR] {agent_name} complete, updates merged\n")
    
    return full_state

def call_agents_parallel_filtered(
    full_state: ChimeraFullState,
    agent_names: List[str]
) -> ChimeraFullState:
    
    print(f"\n[SUPERVISOR] Calling {len(agent_names)} agents in parallel")
    
    for agent_name in agent_names:
        full_state = call_agent_filtered(full_state, agent_name)
    
    return full_state

def merge_agent_result(
    full_state: ChimeraFullState,
    agent_name: str,
    agent_result: Dict
) -> ChimeraFullState:
    
    allowed_updates = {
        "lead_agent": [
            "lead_data", "crm_payload", "lead_status", "analytics_events"
        ],
        "scheduler_agent": [
            "meeting_slots", "provisional_reply", "analytics_events"
        ],
        "stylist_agent": [
            "sanitized_output"
        ],
        "compliance_agent": [
            "sanitized_output", "compliance_flags", "analytics_events"
        ],
        "integration_agent": [
            "analytics_events"
        ],
        "analytics_agent": [
            "conversation_metrics"
        ]
    }
    
    allowed_fields = allowed_updates.get(agent_name, [])
    
    merged_count = 0
    for field in agent_result.keys():
        if field in allowed_fields:
            full_state[field] = agent_result[field]
            print(f"  ✓ Merged: {field}")
            merged_count += 1
        else:
            print(f"  ✗ BLOCKED: {agent_name} tried to update '{field}' (not allowed)")
    
    print(f"  Total merged: {merged_count} fields")
    
    return full_state

def phase_1_initial_analysis(full_state: ChimeraFullState) -> Dict:
    intent = full_state["current_intent"]
    has_email = bool(full_state["entities"].get("email"))
    
    print(f"[PHASE 1] Intent: {intent}, Has email: {has_email}")
    
    if intent == "demo" and has_email:
        return {
            "agents": ["lead_agent", "scheduler_agent"],
            "mode": "parallel",
            "next_phase": "result_collection"
        }
    
    elif intent == "demo":
        return {
            "agents": ["scheduler_agent"],
            "mode": "sequential",
            "next_phase": "result_collection"
        }
    
    elif has_email:
        return {
            "agents": ["lead_agent"],
            "mode": "sequential",
            "next_phase": "result_collection"
        }
    
    else:
        return {
            "agents": [],
            "mode": "skip",
            "next_phase": "post_processing"
        }

def phase_2_result_collection(full_state: ChimeraFullState) -> Dict:
    print(f"[PHASE 2] Reviewing specialist results")
    
    return {
        "agents": ["stylist_agent", "compliance_agent"],
        "mode": "parallel",
        "next_phase": "finalization"
    }

def phase_3_post_processing(full_state: ChimeraFullState) -> Dict:
    print(f"[PHASE 3] All processing complete")
    
    return {
        "agents": [],
        "mode": "done",
        "next_phase": "finalization"
    }
