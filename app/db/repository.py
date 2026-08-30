from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


def create_conversation(
    db: Session,
    user_id: str,
    title: str = "New conversation",
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title=title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_conversation(
    db: Session,
    conversation_id: str,
    user_id: str,
) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )


def get_messages(
    db: Session,
    conversation: Conversation,
) -> list[Message]:
    return list(
        conversation.messages
    )


def add_message(
    db: Session,
    conversation: Conversation,
    role: str,
    content: str,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message