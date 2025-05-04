import os
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
# Use SQLite for development, can be replaced with other DB engines for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./memora.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    items = relationship("Item", back_populates="user")
    
    def __init__(self, id):
        self.id = id

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    url = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    tags = Column(JSON)  # List of tags
    timestamp = Column(DateTime, default=datetime.utcnow)
    embedding = Column(JSON)  # List of floats for vector embedding
    content_type = Column(String, index=True, nullable=True)  # Type of content (social_media, news_article, etc.)
    platform = Column(String, index=True, nullable=True)  # Platform name if applicable (youtube, tiktok, etc.)
    
    user = relationship("User", back_populates="items")
    
    def __init__(self, user_id, url, title, description, tags, embedding, content_type=None, platform=None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.url = url
        self.title = title
        self.description = description
        self.tags = tags
        self.embedding = embedding
        self.content_type = content_type
        self.platform = platform

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(db, user_id):
    """Get or create a user with the given ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user 