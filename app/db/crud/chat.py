from sqlalchemy.orm import Session

from app.db.models.chat_session import ChatSession

from app.db.models.message import Message


def create_chat_session(
    db: Session,
    user_id: int,
    title: str
):

    session = ChatSession(
        user_id=user_id,
        title=title
    )

    db.add(session)

    db.commit()

    db.refresh(session)

    return session


def create_message(
    db: Session,
    session_id: int,
    role: str,
    content: str
):

    message = Message(
        session_id=session_id,
        role=role,
        content=content
    )

    db.add(message)

    db.commit()

    db.refresh(message)

    return message


def get_chat_messages(
    db: Session,
    session_id: int
):

    return db.query(Message).filter(
        Message.session_id == session_id
    ).all()