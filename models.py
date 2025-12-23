"""
Pydantic models for KusiDilve SaaS
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PlanType(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class BookBase(BaseModel):
    isbn13: str
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    price: float = 0.0
    stock: int = 0


class BookClean(BookBase):
    seo_title: str
    description_clean: str
    slug: str
    stock_status: str  # "instock" or "out_of_stock"
    score_seo: int = 0
    sync_date: Optional[datetime] = None


class BookResponse(BookClean):
    id: int
    library_id: int

    class Config:
        from_attributes = True


class LibraryBase(BaseModel):
    name: str
    email: EmailStr
    dilve_user: str
    dilve_password: str
    woocommerce_url: str
    woocommerce_key: str
    woocommerce_secret: str


class LibraryCreate(LibraryBase):
    pass


class LibraryUpdate(BaseModel):
    name: Optional[str] = None
    woocommerce_url: Optional[str] = None
    plan: Optional[PlanType] = None


class LibraryResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    books_count: int
    created_at: datetime
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    total_books: int
    active_books: int
    out_of_stock: int
    seo_score: float
    last_sync: Optional[datetime] = None
    dirty_count: int
    clean_count: int


class SyncRequest(BaseModel):
    library_id: int
    from_date: Optional[str] = None


class SyncResponse(BaseModel):
    processed: int
    cleaned: int
    errors: int
    duration_seconds: float
    status: str  # "success" or "error"


class PricingPlan(BaseModel):
    name: str
    price: float
    features: List[str]
    stripe_price_id: str


class StripeWebhook(BaseModel):
    type: str
    data: dict


class ExportRequest(BaseModel):
    library_id: int
    format: str = "woocommerce"  # "woocommerce" or "generic"


class CSVRow(BaseModel):
    isbn13: str
    sku: str
    title: str
    seo_title: str
    description: str
    regular_price: float
    sale_price: Optional[float] = None
    stock_status: str
    manage_stock: bool = True
    slug: str
    categories: str
    images: Optional[str] = None
