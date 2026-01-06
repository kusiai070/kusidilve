"""
Pydantic models for KusiDilve SaaS
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
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


class KusiBook(BaseModel):
    """Estándar interno de datos KusiDilve"""
    # Identificación y catálogo
    isbn13: str
    sku: str
    post_title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    collection: Optional[str] = None
    publication_year: Optional[str] = None
    language: Optional[str] = None

    # Venta
    regular_price: float
    sale_price: Optional[float] = None
    stock: int = 0
    stock_status: str = "out_of_stock"
    product_type: str = "simple"

    # Contenido / SEO
    post_content: Optional[str] = None
    post_excerpt: Optional[str] = None
    post_name: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    focus_keyword: Optional[str] = None

    # Categorías / tags
    category_main: Optional[str] = None
    category_sub: Optional[str] = None
    tags: Optional[str] = None

    # Imagen
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    image_title: Optional[str] = None

    # Opcionales internos
    thema_code: Optional[str] = None
    thema_description: Optional[str] = None
    ibic_code: Optional[str] = None
    score_seo: int = 0
    is_ai_generated: bool = False

    class Config:
        from_attributes = True


class CSVMappingUpdate(BaseModel):
    mapping: Dict[str, str]


class MappingSuggestionResponse(BaseModel):
    suggested_mapping: Dict[str, str]
    available_headers: List[str]
