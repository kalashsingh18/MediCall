from fastapi import APIRouter, Request, BackgroundTasks, Form, Depends
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.agent.graph import run_agent
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interaction import Interaction
from sqlalchemy import select
import json
import time
from app.database import AsyncSessionLocal


router = APIRouter()

async def log_interaction(patient_phone: str, body: str, ai_response: str, new_summary: str, new_progress: dict):
    """Logs the interaction in a background task."""
    async with AsyncSessionLocal() as db:
        interaction = Interaction(
            patient_ph=patient_phone,
            channel="WHATSAPP",
            transcript={
                "user": body, 
                "ai": ai_response,
                "state": {
                    "summary": new_summary,
                    "progress": new_progress
                }
            }
        )
        db.add(interaction)
        await db.commit()

@router.post("/incoming")
async def handle_whatsapp_incoming(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook for incoming Twilio WhatsApp messages.
    """
    # Twilio sends From as "whatsapp:+14155238886"
    patient_phone = From.replace("whatsapp:", "")
    
    # 1. Fetch chat history and last state
    result = await db.execute(
        select(Interaction)
        .where(Interaction.patient_ph == patient_phone)
        .order_by(Interaction.created_at.desc())
        .limit(5)
    )
    history_records = list(result.scalars().all())
    
    # Extract last known state and check session expiry
    last_summary = ""
    last_progress = {}
    memory_messages = []
    
    if history_records:
        last_interaction = history_records[0]
        
        # Session duration check (e.g., 24 hours)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        # Assuming created_at is aware or we make it aware
        last_time = last_interaction.created_at
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
            
        time_diff = now - last_time
        
        # If the last message was more than 24 hours ago, we treat it as a NEW session greeting-wise
        # but WE KEEP the summary so the AI knows who the patient is.
        is_new_session = time_diff.total_seconds() > (24 * 3600)
        
        last_state = last_interaction.transcript.get("state", {})
        last_summary = last_state.get("summary", "")
        last_progress = last_state.get("progress", {})

        if not is_new_session:
            history_records.reverse()  # Chronological order for messages
            for rec in history_records:
                memory_messages.append(("user", rec.transcript.get("user", "")))
                memory_messages.append(("assistant", rec.transcript.get("ai", "")))
        else:
            print(f"Session expired for {patient_phone}. Starting fresh greeting flow.")
    
    # 2. Run the graph with memory and persistent state
    ai_response, new_summary, new_progress = await run_agent(
        phone=patient_phone,
        channel="WHATSAPP",
        user_text=Body,
        user_name=ProfileName,
        memory_messages=memory_messages,
        initial_summary=last_summary,
        initial_progress=last_progress
    )
    
    # 3. Log the interaction with updated state snapshot (asynchronously)
    background_tasks.add_task(
        log_interaction, 
        patient_phone, 
        Body, 
        ai_response, 
        new_summary, 
        new_progress
    )

    # Build TwiML response
    twiml = MessagingResponse()
    twiml.message(ai_response)
    
    return Response(content=str(twiml), media_type="application/xml")

