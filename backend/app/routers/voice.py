from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
from app.agent.graph import run_agent

router = APIRouter()

@router.websocket("/stream")
async def voice_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams (Voice).
    Twilio connects here to stream bidirectional audio.
    """
    await websocket.accept()
    stream_sid = None
    
    try:
        while True:
            # Wait for Twilio messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            event = message.get("event")
            
            if event == "start":
                stream_sid = message["start"]["streamSid"]
                # Start of call event
                print(f"Call streaming started. Stream SID: {stream_sid}")
                
            elif event == "media":
                # Audio chunk received from caller (base64 encoded mulaw)
                payload = message["media"]["payload"]
                # In a real setup, we would accumulate this payload and send to STT (Deepgram/OpenAI).
                # Once STT detects an utterance end, we call `run_agent(..., channel="VOICE", user_text=STT)`.
                # Then we take the AI text, pass to TTS (ElevenLabs), encode to mulaw base64, 
                # and send back over the WebSocket:
                # await websocket.send_text(json.dumps({
                #     "event": "media",
                #     "streamSid": stream_sid,
                #     "media": {"payload": tts_audio_base64}
                # }))
                pass
                
            elif event == "stop":
                print("Call stream stopped.")
                break
                
    except WebSocketDisconnect:
        print("Call disconnected.")
