from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.services.auth_service import require_user
from app.services.rag_service import answer_question
from app.redis_client import redis_client


router = APIRouter()


class ChatRequest(BaseModel):
    question: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def chat(
    body: ChatRequest,
    username: str = Depends(require_user),
    db: Session = Depends(get_db),
):
    # ==========================
    # 1. 调用 RAG
    # ==========================
    cache_key = f"chat:{username}:{body.question}"

    cached_answer = redis_client.get(cache_key)

    if cached_answer:
        answer = cached_answer
        sources = ["redis-cache"]
    else:
        result = answer_question(body.question)

        if isinstance(result, tuple):
            answer = result[0]
            sources = result[1]
        else:
            answer = result
            sources = []

        answer = str(answer)

        redis_client.setex(
            cache_key,
            300,
            answer,
        )

    # ==========================
    # 3. 确保 answer 是字符串
    # ==========================
    answer = str(answer)

    # ==========================
    # 4. 查询用户
    # ==========================
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise Exception("User not found")

    # ==========================
    # 5. 创建聊天记录
    # ==========================
    chat_message = ChatMessage(
        user_id=user.id,
        question=body.question,
        answer=answer,
    )

    # ==========================
    # 6. 保存 MySQL
    # ==========================
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)

    # ==========================
    # 7. 返回
    # ==========================
    return {
        "answer": answer,
        "sources": sources,
        "message_id": chat_message.id,
    }

@router.delete("/{message_id}")
def delete_chat(
    message_id: int,
    username: str = Depends(require_user),
    db: Session = Depends(get_db),
):
    # 查询当前用户
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 只查询属于当前用户的聊天记录
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.user_id == user.id,
        )
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Chat message not found"
        )

    # 删除聊天记录
    db.delete(message)
    db.commit()

    return {
        "message": "Chat message deleted successfully",
        "message_id": message_id,
    }

@router.get("/history")
def chat_history(
    page: int = 1,
    page_size: int = 10,
    username: str = Depends(require_user),
    db: Session = Depends(get_db),
):
    # 参数校验
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 10

    if page_size > 100:
        page_size = 100

    # 查询当前用户
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 查询当前用户的聊天记录
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
    )

    # 总记录数
    total = query.count()

    # 计算偏移量
    offset = (page - 1) * page_size

    # 分页查询
    messages = (
        query
        .order_by(ChatMessage.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "id": message.id,
                "question": message.question,
                "answer": message.answer,
                "created_at": message.created_at,
            }
            for message in messages
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }