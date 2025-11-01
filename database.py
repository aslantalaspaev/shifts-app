from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    ldap = Column(String, unique=True, index=True)
    first_name = Column(String)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Shift(Base):
    __tablename__ = "shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_telegram_id = Column(String, index=True)
    shift_date = Column(String)  # YYYY-MM-DD
    shift_type = Column(String)  # "день", "ночь", или "часы"
    start_time = Column(String, nullable=True)  # HH:MM (для типа "часы")
    end_time = Column(String, nullable=True)    # HH:MM (для типа "часы")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShiftRequest(Base):
    __tablename__ = "shift_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, index=True)
    requester_telegram_id = Column(String, index=True)
    creator_telegram_id = Column(String, index=True)
    status = Column(String, default="pending")  # "pending", "approved", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShiftHistory(Base):
    __tablename__ = "shift_history"
    
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer)
    creator_telegram_id = Column(String)
    requester_telegram_id = Column(String, nullable=True)
    action = Column(String)  # "created", "approved", "rejected", "cancelled"
    shift_date = Column(String)
    shift_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
