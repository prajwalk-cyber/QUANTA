"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import init_db
from routers import auth, handshake, comms, signing, audit, system, quantum_router, channel_router


from fastapi.responses import FileResponse
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    init_db()
    yield


app = FastAPI(title="QUANTA Backend API", lifespan=lifespan)

@app.get("/")
async def serve_frontend():
    frontend_index = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))
    return FileResponse(frontend_index)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.auth_router)
app.include_router(auth.keys_router)
app.include_router(handshake.router)
app.include_router(comms.router)
app.include_router(signing.router)
app.include_router(audit.router)
app.include_router(system.router)
app.include_router(quantum_router.router)
app.include_router(channel_router.router)
