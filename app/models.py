from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

Base = declarative_base()

class DocumentAnalysis(Base):
    __tablename__ = "document_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_text = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    model_used = Column(String, default="mistralai/Mistral-7B-Instruct-v0.2")
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    total_requests = Column(Integer, default=0)
    daily_requests = Column(Integer, default=0)
    last_request_date = Column(DateTime, nullable=True)

    is_admin = Column(Boolean, default=False)

user_id = Column(Integer, ForeignKey("users.id"))
user = relationship("User")

from sqlalchemy import Boolean
import secrets

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    @staticmethod
    def generate_key():
        return "ea_" + secrets.token_hex(32)