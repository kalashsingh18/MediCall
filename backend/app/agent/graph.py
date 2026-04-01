from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from datetime import date, datetime
from typing import Optional
from app.core.config import settings
from app.agent.state import AgentState
from app.services.bot_tools import (
    get_doctors,
    get_doctor_details,
    check_available_slots,
    book_appointment,
    reschedule_appointment,
    get_clinic_rules,
    get_patient_history,
    get_clinic_info,
    get_queue_status,
    get_payment_link,
    get_triage_recommendation,
    get_specialists_by_category,
    confirm_payment,
    add_to_waitlist,
    cancel_appointment
)
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode

# Initialize LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    api_key=settings.GROQ_API_KEY,
    temperature=0.1
)

tools = [
    get_doctors, 
    get_doctor_details, 
    check_available_slots, 
    book_appointment, 
    reschedule_appointment, 
    get_clinic_rules,
    get_patient_history,
    get_clinic_info,
    get_queue_status,
    get_payment_link,
    get_triage_recommendation,
    get_specialists_by_category,
    confirm_payment,
    add_to_waitlist,
    cancel_appointment
]
llm_with_tools = llm.bind_tools(tools)

# --- NODES ---

async def summarize_history(state: AgentState):
    """
    Summarizes the conversation history if it exceeds a certain length.
    """
    messages = state["messages"]
    # We summarize if history is > 8 messages (4 turns)
    if len(messages) <= 8:
        return {"messages": []} # No-op
    
    # Existing summary
    existing_summary = state.get("summary", "")
    
    # Create summarization prompt
    summary_prompt = (
        f"Summarize the following conversation concisely, focusing on "
        f"essential details like patient name, symptoms, doctor choice, and appointment status (including payment & waitlist state). "
        f"Existing summary: {existing_summary}\n\n"
        f"New messages to incorporate: {messages}"
    )
    
    response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
    
    # We keep the last 2 messages for immediate context, but the rest is summarized
    # In LangGraph with Annotated[Sequence, add], we return the NEW messages.
    # To 'delete' old ones is tricky, but here we just update the 'summary' field.
    return {"summary": response.content}

async def chatbot(state: AgentState):
    """
    The main receptionist node.
    """
    current_date = date.today().strftime("%A, %B %d, %Y")
    summary = state.get("summary", "")
    booking_prog = state.get("booking_progress", {})
    history = state["messages"]
    
    # Logic to prevent repetitive greetings: 
    is_start_of_conversation = len(history) <= 1
    
    greeting_rule = ""
    if is_start_of_conversation:
        greeting_rule = """
        - START OF SESSION: Use `get_patient_history` to identify the user.
        - GREETING: Use "Welcome back [Name]!" or "Welcome to MediCall!" exactly ONCE."""
    else:
        greeting_rule = """
        - ONGOING SESSION: You have already greeted the user. 
        - DO NOT REPEAT "Welcome back", "How can I help you", or any introductory boilerplate. 
        - DO NOT call `get_patient_history` again if you already have the info.
        - PROCEED IMMEDIATELY to the user's request."""

    system_prompt = f"""
    You are the Senior Receptionist for MediCall Clinic. Today is {current_date}.
    {greeting_rule}
    
    CORE PROTOCOLS:
    1. TRIAGE: If the user mentions symptoms, you MAY use the `get_triage_recommendation` tool if appropriate.
Do NOT manually format function calls. Use tools only when needed.
    2. SPECIALISTS: If they need a specific type of doctor, use `get_specialists_by_category`.
    3. BOOKING: book_appointment -> get_payment_link -> confirm_payment.
    4. QUEUE/PAYMENT/CANCEL: Use `get_queue_status`, `get_payment_link`, or `cancel_appointment` as requested.
    5. WAITLIST: If no slots are found using `check_available_slots`, offer the Waitlist and use `add_to_waitlist`.
    
    RULES:
    - Identify users with `get_patient_history` first.
    - Propose past doctors if found in history.
    - Be professional, concise, and always respond in the user's language.
    
    CURRENT STATE:
    - History Summary: {summary or "New conversation"}
    - Extracted Data: {booking_prog or "None yet"}
    - Patient Phone: {state['patient_phone']}
    """

    
    # Assemble messages
    history = state["messages"]
    if summary:
        history = history[-6:]
        
    messages = [SystemMessage(content=system_prompt)] + list(history)
    
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def extract_progress(state: AgentState):
    """
    Extracts structured booking data (Doctor, Date, Time) from the recent conversation.
    """
    history = state["messages"][-3:] # Last exchange
    extract_prompt = (
        "Extract the following details from this medical booking conversation into a JSON object: "
        "'doctor_id', 'doctor_name', 'date', 'time', 'patient_name'. "
        "Only extract if explicitly mentioned. If not found, leave as null. "
        f"Conversation: {history}"
    )
    # We use a non-tool bound LLM for extraction to keep it focused
    response = await llm.ainvoke([HumanMessage(content=extract_prompt)])
    
    import json
    try:
        # Simple extraction logic (can be refined with Pydantic)
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            new_prog = json.loads(json_match.group())
            # Merge with existing progress (non-null overrides)
            current_prog = state.get("booking_progress", {}).copy()
            for k, v in new_prog.items():
                if v: current_prog[k] = v
            return {"booking_progress": current_prog}
    except:
        pass
    return {"booking_progress": state.get("booking_progress", {})}


# --- GRAPH CONSTRUCTION ---

graph_builder = StateGraph(AgentState)

graph_builder.add_node("summarize", summarize_history)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_node("extractor", extract_progress)

graph_builder.set_entry_point("summarize")
graph_builder.add_edge("summarize", "chatbot")

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "extractor"

graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", "extractor"])
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("extractor", END)


agent_graph = graph_builder.compile()

# --- RUNNER ---

async def run_agent(phone: str, channel: str, user_text: str, user_name: Optional[str] = None, 
                    memory_messages: list = None, initial_summary: str = "", initial_progress: dict = None):
    """
    Entry point for the AI agent with state persistence support.
    """
    # Initialize state with properly typed messages
    initial_messages = []
    if memory_messages:
        for msg in memory_messages:
            if isinstance(msg, (tuple, list)) and len(msg) == 2:
                role, content = msg
                if role == "user": initial_messages.append(HumanMessage(content=content))
                elif role == "assistant": initial_messages.append(AIMessage(content=content))
            else:
                initial_messages.append(msg)
                
    initial_messages.append(HumanMessage(content=user_text))

    initial_state = {
        "messages": initial_messages,
        "summary": initial_summary or "",
        "booking_progress": initial_progress or {},
        "patient_phone": phone,
        "user_name": user_name,
        "channel": channel
    }
    
    final_state = await agent_graph.ainvoke(initial_state)
    
    # Return the last AI content and the new state for persistence
    last_msg = final_state["messages"][-1]
    return last_msg.content, final_state.get("summary", ""), final_state.get("booking_progress", {})
