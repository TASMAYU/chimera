from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add

class ChimeraFullState(TypedDict):
    session_id: str
    messages: Annotated[List[Dict], add]
    current_intent: str
    confidence_score: float
    next_action: str
    previous_agent: str
    iteration_count: int
    entities: Dict
    lead_data: Optional[Dict]
    lead_status: str
    crm_payload: Optional[Dict]
    meeting_slots: Optional[List[Dict]]
    provisional_reply: str
    sanitized_output: str
    brand_profile: Dict
    compliance_flags: List[str]
    analytics_events: Annotated[List[Dict], add]
    conversation_metrics: Dict
    retrieved_context: List[str]
    context_used: bool
    agent_queue: List[str]
    execution_mode: str
    supervisor_phase: str
    parallel_results: Dict[str, Dict]
    _api_credentials: Optional[Dict]
    _tenant_config: Optional[Dict]


class ConversationAgentState(TypedDict):
    session_id: str
    messages: List[Dict]
    brand_profile: Dict


class LeadAgentState(TypedDict):
    entities: Dict
    messages: List[Dict]


class SchedulerAgentState(TypedDict):
    entities: Dict
    current_intent: str


class StylistAgentState(TypedDict):
    provisional_reply: str
    brand_profile: Dict


class ComplianceAgentState(TypedDict):
    sanitized_output: str


class IntegrationAgentState(TypedDict):
    crm_payload: Optional[Dict]
    meeting_slots: Optional[List[Dict]]


class AnalyticsAgentState(TypedDict):
    analytics_events: List[Dict]
    conversation_metrics: Dict
    session_id: str
