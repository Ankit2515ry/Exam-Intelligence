from sqlalchemy.orm import Session

from app.db.models.document import Document


def create_document(
    db: Session,
    title: str,
    filename: str,
    file_path: str,
    subject: str,
    uploaded_by: int,
    document_uuid: str
):

    document = Document(

        title=title,

        filename=filename,

        file_path=file_path,

        subject=subject,

        uploaded_by=uploaded_by,

        document_uuid=document_uuid
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    return document


def get_document(
    db: Session,
    document_id: int
):

    return db.query(Document).filter(
        Document.id == document_id
    ).first()


def get_user_documents(
    db: Session,
    user_id: int
):

    return db.query(Document).filter(
        Document.uploaded_by == user_id
    ).all()


def delete_document(
    db: Session,
    document_id: int
):

    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document:

        db.delete(document)

        db.commit()

    return document

def get_document_by_uuid(
    db: Session,
    document_uuid: str
):

    return db.query(Document).filter(
        Document.document_uuid == document_uuid
    ).first()

def delete_document_record(
    db: Session,
    document: Document
):

    db.delete(document)

    db.commit()