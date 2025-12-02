from core.state import (
    ChimeraFullState,
    ConversationAgentState,
    LeadAgentState,
    SchedulerAgentState,
    StylistAgentState,
    ComplianceAgentState,
    IntegrationAgentState,
    AnalyticsAgentState
)

from typing import Dict
import copy
from datetime import datetime


class StateFilter:

    @staticmethod
    def for_conversation_agent(full_state: ChimeraFullState) -> ConversationAgentState:
        filtered = {
            "session_id": full_state["session_id"],
            "messages": copy.deepcopy(full_state["messages"]),
            "brand_profile": copy.deepcopy(full_state["brand_profile"])
        }
        StateFilter._log_access("conversation_agent", filtered)
        return filtered

    @staticmethod
    def for_lead_agent(full_state: ChimeraFullState) -> LeadAgentState:
        filtered = {
            "entities": copy.deepcopy(full_state["entities"]),
            "messages": copy.deepcopy(full_state["messages"])
        }
        StateFilter._log_access("lead_agent", filtered)
        return filtered

    @staticmethod
    def for_scheduler_agent(full_state: ChimeraFullState) -> SchedulerAgentState:
        filtered = {
            "entities": copy.deepcopy(full_state["entities"]),
            "current_intent": full_state["current_intent"]
        }
        StateFilter._log_access("scheduler_agent", filtered)
        return filtered

    @staticmethod
    def for_stylist_agent(full_state: ChimeraFullState) -> StylistAgentState:
        filtered = {
            "provisional_reply": full_state["provisional_reply"],
            "brand_profile": copy.deepcopy(full_state["brand_profile"])
        }
        StateFilter._log_access("stylist_agent", filtered)
        return filtered

    @staticmethod
    def for_compliance_agent(full_state: ChimeraFullState) -> ComplianceAgentState:
        filtered = {
            "sanitized_output": full_state["sanitized_output"]
        }
        StateFilter._log_access("compliance_agent", filtered)
        return filtered

    @staticmethod
    def for_integration_agent(full_state: ChimeraFullState) -> IntegrationAgentState:
        filtered = {
            "crm_payload": copy.deepcopy(full_state.get("crm_payload")),
            "meeting_slots": copy.deepcopy(full_state.get("meeting_slots"))
        }
        StateFilter._log_access("integration_agent", filtered)
        return filtered

    @staticmethod
    def for_analytics_agent(full_state: ChimeraFullState) -> AnalyticsAgentState:
        filtered = {
            "analytics_events": copy.deepcopy(full_state["analytics_events"]),
            "conversation_metrics": copy.deepcopy(full_state.get("conversation_metrics", {})),
            "session_id": full_state["session_id"]
        }
        StateFilter._log_access("analytics_agent", filtered)
        return filtered

    @staticmethod
    def _log_access(agent_name: str, filtered_state: Dict):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = list(filtered_state.keys())
        data_size = len(str(filtered_state))

        print(f"[SECURITY AUDIT] {timestamp}")
        print(f"  Agent: {agent_name}")
        print(f"  Fields accessed: {fields}")
        print(f"  Data size: {data_size} bytes")

    @staticmethod
    def mask_sensitive_for_logging(data: Dict) -> Dict:
        masked = copy.deepcopy(data)

        if "entities" in masked and "email" in masked["entities"]:
            email = masked["entities"]["email"]
            if "@" in email:
                name, domain = email.split("@")
                masked["entities"]["email"] = f"{name[0]}***@{domain}"

        if "crm_payload" in masked and "api_key" in masked.get("crm_payload", {}):
            masked["crm_payload"]["api_key"] = "***REDACTED***"

        return masked
