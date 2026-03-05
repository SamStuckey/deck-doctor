from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import upload, cards, events

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Deck Doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(events.router, prefix="/api")
