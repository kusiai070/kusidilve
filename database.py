"""
SQLAlchemy models and database setup for KusiDilve
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kusi_dilve.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Library(Base):
    __tablename__ = "libraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    dilve_user = Column(String)
    dilve_password = Column(String)  # TODO: Encrypt in production
    woocommerce_url = Column(String)
    woocommerce_key = Column(String)
    woocommerce_secret = Column(String)  # TODO: Encrypt in production
    plan = Column(String, default="basic")  # basic, pro, premium
    books_count = Column(Integer, default=0)
    
    # Mapping and AI Config
    csv_mapping = Column(Text, nullable=True)  # JSON string
    use_ai_seo = Column(Boolean, default=False)
    gemini_api_key = Column(String, nullable=True)
    openai_api_key = Column(String, nullable=True)
    anthropic_api_key = Column(String, nullable=True)
    has_own_dilve_credentials = Column(Boolean, default=False)  # Para Bloque 4
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    books = relationship("Book", back_populates="library", cascade="all, delete-orphan")
    syncs = relationship("SyncLog", back_populates="library", cascade="all, delete-orphan")

    class Config:
        from_attributes = True


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), index=True)
    isbn13 = Column(String, index=True)
    title = Column(String)
    author = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_clean = Column(Text, nullable=True)
    price = Column(Float, default=0.0)
    sale_price = Column(Float, nullable=True)
    stock = Column(Integer, default=0)
    stock_status = Column(String, default="out_of_stock")  # instock, out_of_stock
    
    # KusiBook Extended Fields
    publisher = Column(String, nullable=True)
    collection = Column(String, nullable=True)
    publication_year = Column(String, nullable=True)
    language = Column(String, nullable=True)
    
    # Content / SEO
    post_excerpt = Column(Text, nullable=True)
    seo_description = Column(Text, nullable=True)
    focus_keyword = Column(String, nullable=True)
    
    # Categorías
    category_main = Column(String, nullable=True)
    category_sub = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    
    # Media
    image_url = Column(String, nullable=True)
    image_alt = Column(String, nullable=True)
    image_title = Column(String, nullable=True)

    seo_title = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    score_seo = Column(Integer, default=0)
    is_dirty = Column(Boolean, default=True)
    sync_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    library = relationship("Library", back_populates="books")

    class Config:
        from_attributes = True


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), index=True)
    processed = Column(Integer, default=0)
    cleaned = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, success, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    library = relationship("Library", back_populates="syncs")

    class Config:
        from_attributes = True


class StripeSubscription(Base):
    __tablename__ = "stripe_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"), unique=True)
    stripe_customer_id = Column(String, unique=True)
    stripe_subscription_id = Column(String, unique=True)
    plan = Column(String)
    status = Column(String)  # active, canceled, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class Config:
        from_attributes = True


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
