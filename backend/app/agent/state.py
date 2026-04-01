from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # The message history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # History summary to keep context window small
    summary: str
    
    # Structured booking progress (doctor_id, date, time, etc.)
    booking_progress: Dict[str, Any]
    
    # Metadata about the user
    patient_phone: str
    user_name: Optional[str]
    channel: str # "VOICE" or "WHATSAPP"
