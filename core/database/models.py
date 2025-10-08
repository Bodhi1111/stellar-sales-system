from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Transcript(Base):
    __tablename__ = 'transcripts'

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, nullable=False,
                         index=True)  # transcript_id from header
    filename = Column(String, nullable=False)
    full_text = Column(Text, nullable=True)

    # Storing structured data from our agents
    extracted_data = Column(JSON)
    social_content = Column(JSON)
    crm_data = Column(JSON)  # NEW: Added field to store CRMAgent output

    # Storing the generated email draft
    email_draft = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transcript(id={self.id}, external_id='{self.external_id}', filename='{self.filename}')>"
