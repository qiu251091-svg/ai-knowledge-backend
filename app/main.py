from app.core.database import Base, engine
from app.models.user import User
from app.models.chat_message import ChatMessage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, chat, documents

app = FastAPI(title="AI Knowledge Backend", version="1.0.0")
Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(
    documents.router,
    prefix="/api/documents",
    tags=["documents"],
)
