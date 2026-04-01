from twilio.rest import Client
from app.core.config import settings

def send_whatsapp_message(to_phone: str, body: str):
    """
    Sends a WhatsApp message via Twilio. 
    Fallbacks to simulation mode if credentials are missing.
    """
    if not settings.TWILIO_ACCOUNT_SID or "AC" not in settings.TWILIO_ACCOUNT_SID:
        print(f"[SIMULATION] To {to_phone}: {body}")
        return "sim_sid_123"
    
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # Ensure phone doesn't have double prefix
        clean_phone = to_phone.replace("whatsapp:", "")
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=body,
            to=f"whatsapp:{clean_phone}"
        )
        return message.sid
    except Exception as e:
        print(f"Error sending WhatsApp to {to_phone}: {e}")
        return None
