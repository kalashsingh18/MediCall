from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_tables
from app.routers import auth, clinic, doctors, patients, appointments, queue, visits, prescriptions, billing, dashboard, whatsapp, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables
    await create_tables()
    yield
    # Shutdown (nothing needed)


app = FastAPI(
    title="MediCall API",
    description="India-first Clinic Management Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(clinic.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(queue.router)
app.include_router(visits.router)
app.include_router(prescriptions.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp-bot"])
app.include_router(voice.router, prefix="/voice", tags=["voice-bot"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": "MediCall API", "version": "1.0.0"}
