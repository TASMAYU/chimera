"""
core/graph_builder.py
"""

from langgraph.graph import StateGraph, END
from core.state import ChimeraFullState
from agents.supervisor_agent import supervisor_agent
from agents.conversation_agent import conversation_agent


def build_supervisor_graph(knowledge_base):
    print("\n" + "="*60)
    print("BUILDING SECURE SUPERVISOR GRAPH")
    print("="*60 + "\n")
    
    workflow = StateGraph(ChimeraFullState)
    
    workflow.add_node(
        "conversation",
        lambda state: conversation_agent_wrapper(state, knowledge_base)
    )
    
    workflow.add_node("supervisor", supervisor_agent)
    
    workflow.set_entry_point("conversation")
    
    workflow.add_edge("conversation", "supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_action"],
        {
            "supervisor": "supervisor",
            "analytics": END
        }
    )
    
    compiled = workflow.compile()
    
    print("✅ Secure graph compiled!")
    print("="*60 + "\n")
    
    return compiled


def conversation_agent_wrapper(full_state: ChimeraFullState, knowledge_base):
    from core.state_filter import StateFilter
    
    filtered_state = StateFilter.for_conversation_agent(full_state)
    
    result = conversation_agent(filtered_state, knowledge_base)
    
    full_state["provisional_reply"] = result.get("provisional_reply", "")
    full_state["current_intent"] = result.get("current_intent", "question")
    full_state["confidence_score"] = result.get("confidence_score", 0.0)
    full_state["entities"] = result.get("entities", {})
    full_state["retrieved_context"] = result.get("retrieved_context", [])
    full_state["context_used"] = result.get("context_used", False)
    
    if "analytics_events" in result:
        full_state["analytics_events"].extend(result["analytics_events"])
    
    full_state["next_action"] = "supervisor"
    full_state["previous_agent"] = "conversation"
    
    return full_state
