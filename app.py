"""
KusiDilve SaaS - FastAPI Backend
Limpieza DILVE → WooCommerce Sync
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import csv
import io
import logging
import os
from typing import List, Optional
import asyncio

# Imports locales
from database import get_db, engine, Base, Library, Book, SyncLog, StripeSubscription
from models import (
    LibraryCreate, LibraryResponse, DashboardMetrics, SyncRequest, SyncResponse,
    BookResponse, PricingPlan, ExportRequest
)
from csv_cleaner import CSVCleaner
from dilve_client import DilveClient, DilveSync
from woocommerce_sync import WooCommerceClient, WooCommerceSync
from mapping_utils import normalize_header, suggest_mapping
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="KusiDilve SaaS",
    description="Limpieza DILVE → WooCommerce Sync para librerías españolas",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs("templates", exist_ok=True)
os.makedirs("data", exist_ok=True)


# ============================================================================
# RUTAS PÚBLICAS
# ============================================================================

@app.get("/")
async def root():
    """Redirige a dashboard"""
    return {"message": "KusiDilve SaaS API", "docs": "/docs"}


@app.get("/pricing")
async def get_pricing():
    """Obtiene planes de precios"""
    plans = [
        {
            "name": "Básico",
            "price": 9.0,
            "features": [
                "CSV limpio mensual",
                "Hasta 5.000 libros",
                "Soporte por email",
                "Limpieza UTF-8/HTML"
            ],
            "stripe_price_id": "price_basic_monthly"
        },
        {
            "name": "PRO",
            "price": 29.0,
            "features": [
                "Todo Básico +",
                "Sync stock automático ⭐",
                "Hasta 50.000 libros",
                "Soporte prioritario",
                "API REST acceso"
            ],
            "stripe_price_id": "price_pro_monthly"
        },
        {
            "name": "Premium",
            "price": 59.0,
            "features": [
                "Todo PRO +",
                "Alertas en tiempo real",
                "Sincronización cada hora",
                "Hasta 500.000 libros",
                "Soporte 24/7",
                "Consultoría SEO"
            ],
            "stripe_price_id": "price_premium_monthly"
        }
    ]
    return {"plans": plans}


# ============================================================================
# RUTAS AUTENTICADAS - LIBRERÍAS
# ============================================================================

@app.post("/api/libraries", response_model=LibraryResponse)
async def create_library(library: LibraryCreate, db: Session = Depends(get_db)):
    """Crea nueva librería"""
    try:
        # Verifica que no exista
        existing = db.query(Library).filter(Library.email == library.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")

        # Crea librería
        db_library = Library(
            name=library.name,
            email=library.email,
            dilve_user=library.dilve_user,
            dilve_password=library.dilve_password,
            woocommerce_url=library.woocommerce_url,
            woocommerce_key=library.woocommerce_key,
            woocommerce_secret=library.woocommerce_secret,
            plan="basic"
        )
        db.add(db_library)
        db.commit()
        db.refresh(db_library)

        logger.info(f"Library created: {db_library.id} - {library.name}")
        return db_library

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/libraries/{library_id}", response_model=LibraryResponse)
async def get_library(library_id: int, db: Session = Depends(get_db)):
    """Obtiene librería por ID"""
    library = db.query(Library).filter(Library.id == library_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="Librería no encontrada")
    return library


# ============================================================================
# DASHBOARD & MÉTRICAS
# ============================================================================

@app.get("/api/dashboard/{library_id}")
async def get_dashboard(library_id: int, db: Session = Depends(get_db)):
    """Obtiene métricas del dashboard"""
    try:
        library = db.query(Library).filter(Library.id == library_id).first()
        if not library:
            raise HTTPException(status_code=404, detail="Librería no encontrada")

        # Calcula métricas
        total_books = db.query(Book).filter(Book.library_id == library_id).count()
        active_books = db.query(Book).filter(
            Book.library_id == library_id,
            Book.stock > 0
        ).count()
        out_of_stock = total_books - active_books
        dirty_count = db.query(Book).filter(
            Book.library_id == library_id,
            Book.is_dirty == True
        ).count()
        clean_count = total_books - dirty_count

        # SEO score promedio
        books = db.query(Book).filter(Book.library_id == library_id).all()
        avg_seo = sum(b.score_seo for b in books) / len(books) if books else 0

        return {
            "total_books": total_books,
            "active_books": active_books,
            "out_of_stock": out_of_stock,
            "dirty_count": dirty_count,
            "clean_count": clean_count,
            "seo_score": round(avg_seo, 1),
            "last_sync": library.last_sync,
            "plan": library.plan,
            "percentage_clean": round((clean_count / total_books * 100) if total_books > 0 else 0, 1)
        }

    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SINCRONIZACIÓN DILVE
# ============================================================================

@app.post("/api/sync/dilve/{library_id}")
async def sync_dilve(
    library_id: int,
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sincroniza cambios desde DILVE"""
    try:
        library = db.query(Library).filter(Library.id == library_id).first()
        if not library:
            raise HTTPException(status_code=404, detail="Librería no encontrada")

        # Crea cliente DILVE
        dilve_client = DilveClient(library.dilve_user, library.dilve_password)
        dilve_sync = DilveSync(dilve_client)

        # Sincroniza en background
        background_tasks.add_task(
            _sync_dilve_background,
            library_id,
            dilve_sync,
            request.from_date or "2025-12-22",
            db
        )

        return {
            "status": "processing",
            "message": "Sincronización iniciada",
            "library_id": library_id
        }

    except Exception as e:
        logger.error(f"Error syncing DILVE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _sync_dilve_background(library_id: int, dilve_sync: DilveSync, from_date: str, db: Session):
    """Sincronización en background"""
    try:
        start_time = datetime.utcnow()

        # Obtiene registros de DILVE
        result = await dilve_sync.sync_from_date(from_date)

        if result.get("status") != "success":
            logger.error(f"DILVE sync failed: {result}")
            return

        records = result.get("records", [])
        logger.info(f"DILVE sync: {len(records)} registros")

        # Limpia registros
        cleaned_records, error_count = CSVCleaner.clean_csv(records)

        # Guarda en BD
        for cleaned in cleaned_records:
            existing = db.query(Book).filter(
                Book.library_id == library_id,
                Book.isbn13 == cleaned["isbn13"]
            ).first()

            if existing:
                existing.title = cleaned["title"]
                existing.author = cleaned["author"]
                existing.description = cleaned["description"]
                existing.description_clean = cleaned["description_clean"]
                existing.price = cleaned["price"]
                existing.stock = cleaned["stock"]
                existing.stock_status = cleaned["stock_status"]
                existing.seo_title = cleaned["seo_title"]
                existing.slug = cleaned["slug"]
                existing.score_seo = cleaned["score_seo"]
                existing.is_dirty = False
                existing.sync_date = datetime.utcnow()
            else:
                book = Book(
                    library_id=library_id,
                    isbn13=cleaned["isbn13"],
                    title=cleaned["title"],
                    author=cleaned["author"],
                    description=cleaned["description"],
                    description_clean=cleaned["description_clean"],
                    price=cleaned["price"],
                    stock=cleaned["stock"],
                    stock_status=cleaned["stock_status"],
                    seo_title=cleaned["seo_title"],
                    slug=cleaned["slug"],
                    score_seo=cleaned["score_seo"],
                    is_dirty=False,
                    sync_date=datetime.utcnow()
                )
                db.add(book)

        # Actualiza librería
        library = db.query(Library).filter(Library.id == library_id).first()
        library.books_count = len(cleaned_records)
        library.last_sync = datetime.utcnow()

        # Registra sync log
        duration = (datetime.utcnow() - start_time).total_seconds()
        sync_log = SyncLog(
            library_id=library_id,
            processed=len(records),
            cleaned=len(cleaned_records),
            errors=error_count,
            duration_seconds=duration,
            status="success"
        )
        db.add(sync_log)
        db.commit()

        logger.info(f"DILVE sync completed: {len(cleaned_records)} cleaned, {error_count} errors")

    except Exception as e:
        logger.error(f"Background sync error: {e}")


# ============================================================================
# SINCRONIZACIÓN WOOCOMMERCE
# ============================================================================

@app.post("/api/sync/woocommerce/{library_id}")
async def sync_woocommerce(
    library_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sincroniza productos a WooCommerce"""
    try:
        library = db.query(Library).filter(Library.id == library_id).first()
        if not library:
            raise HTTPException(status_code=404, detail="Librería no encontrada")

        # Verifica plan
        if library.plan == "basic":
            raise HTTPException(status_code=403, detail="Plan Básico no incluye sync WooCommerce")

        # Crea cliente WooCommerce
        wc_client = WooCommerceClient(
            library.woocommerce_url,
            library.woocommerce_key,
            library.woocommerce_secret
        )

        # Sincroniza en background
        background_tasks.add_task(
            _sync_woocommerce_background,
            library_id,
            wc_client,
            db
        )

        return {
            "status": "processing",
            "message": "Sincronización WooCommerce iniciada",
            "library_id": library_id
        }

    except Exception as e:
        logger.error(f"Error syncing WooCommerce: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _sync_woocommerce_background(library_id: int, wc_client: WooCommerceClient, db: Session):
    """Sincronización WooCommerce en background"""
    try:
        start_time = datetime.utcnow()

        # Obtiene libros limpios
        books = db.query(Book).filter(
            Book.library_id == library_id,
            Book.is_dirty == False
        ).all()

        books_data = [
            {
                "isbn13": b.isbn13,
                "sku": f"LIB-{b.isbn13[-6:]}",
                "title": b.title,
                "author": b.author,
                "description": b.description,
                "description_clean": b.description_clean,
                "price": b.price,
                "stock": b.stock,
                "stock_status": b.stock_status,
                "seo_title": b.seo_title,
                "slug": b.slug,
                "score_seo": b.score_seo,
                "categories": "Ficción"
            }
            for b in books
        ]

        # Sincroniza
        wc_sync = WooCommerceSync(wc_client)
        result = await wc_sync.sync_products(books_data)

        # Registra log
        duration = (datetime.utcnow() - start_time).total_seconds()
        sync_log = SyncLog(
            library_id=library_id,
            processed=len(books_data),
            cleaned=result.get("created", 0) + result.get("updated", 0),
            errors=result.get("errors", 0),
            duration_seconds=duration,
            status="success" if result.get("status") == "success" else "partial"
        )
        db.add(sync_log)
        db.commit()

        logger.info(f"WooCommerce sync completed: {result}")

    except Exception as e:
        logger.error(f"Background WooCommerce sync error: {e}")


# ============================================================================
# EXPORTAR CSV
# ============================================================================

@app.get("/api/export/woocommerce/{library_id}")
async def export_woocommerce_csv(library_id: int, db: Session = Depends(get_db)):
    """Exporta CSV en formato WooCommerce"""
    try:
        books = db.query(Book).filter(
            Book.library_id == library_id,
            Book.is_dirty == False
        ).all()

        if not books:
            raise HTTPException(status_code=404, detail="No hay libros limpios para exportar")

        books_data = [
            {
                "isbn13": b.isbn13,
                "sku": f"LIB-{b.isbn13[-6:]}" if b.isbn13 else "LIB-000000",
                "post_title": b.title,
                "author": b.author,
                "publisher": b.publisher,
                "collection": b.collection,
                "publication_year": b.publication_year,
                "language": b.language,
                "regular_price": b.price,
                "sale_price": b.sale_price,
                "stock": b.stock,
                "stock_status": b.stock_status,
                "post_content": b.description_clean,
                "post_excerpt": b.post_excerpt,
                "post_name": b.slug,
                "seo_title": b.seo_title,
                "seo_description": b.seo_description,
                "focus_keyword": b.focus_keyword,
                "category_main": b.category_main,
                "category_sub": b.category_sub,
                "tags": b.tags,
                "image_url": b.image_url,
                "image_alt": b.image_alt,
                "image_title": b.image_title
            }
            for b in books
        ]

        # Genera CSV
        csv_content = CSVCleaner.to_woocommerce_csv(books_data)

        # Retorna como descarga
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=woocommerce_export.csv"}
        )

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/wp-all-import/{library_id}")
async def export_wp_all_import_csv(library_id: int, db: Session = Depends(get_db)):
    """Exporta CSV en formato WP All Import (drag&drop Step 4)"""
    try:
        from csv_wpallimport import WPAllImportConverter

        books = db.query(Book).filter(
            Book.library_id == library_id,
            Book.is_dirty == False
        ).all()

        if not books:
            raise HTTPException(status_code=404, detail="No hay libros limpios para exportar")

        books_data = [
            {
                "isbn13": b.isbn13,
                "titulo": b.title,
                "autor": b.author,
                "resumen": b.description_clean,
                "precio": str(b.price),
                "stock": str(b.stock),
                "materia_ibic": "Ficción"
            }
            for b in books
        ]

        # Convierte a WP All Import
        csv_content = WPAllImportConverter.to_wp_all_import_csv(books_data)

        # Retorna como descarga
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=wp_all_import_ready.csv"}
        )

    except Exception as e:
        logger.error(f"Error exporting WP All Import CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UPLOAD CSV
# ============================================================================

@app.post("/api/libraries/{library_id}/csv-mapping")
async def update_csv_mapping(
    library_id: int,
    mapping_data: CSVMappingUpdate,
    db: Session = Depends(get_db)
):
    """Guarda el mapeo de columnas para una librería"""
    library = db.query(Library).filter(Library.id == library_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="Librería no encontrada")
    
    library.csv_mapping = json.dumps(mapping_data.mapping)
    db.commit()
    return {"status": "success", "message": "Mapping actualizado"}

@app.post("/api/upload/csv/{library_id}")
async def upload_csv(
    library_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Sube y procesa CSV con soporte para Mapping Personalizado"""
    try:
        library = db.query(Library).filter(Library.id == library_id).first()
        if not library:
            raise HTTPException(status_code=404, detail="Librería no encontrada")

        content = await file.read()
        csv_text = content.decode('utf-8', errors='ignore')

        reader = csv.DictReader(io.StringIO(csv_text))
        headers = reader.fieldnames
        rows = list(reader)

        if not headers:
            raise HTTPException(status_code=400, detail="CSV sin cabeceras")

        # Recuperar o sugerir mapping
        current_mapping = {}
        if library.csv_mapping:
            current_mapping = json.loads(library.csv_mapping)
        else:
            current_mapping = suggest_mapping(headers)
            # No lo guardamos automáticamente, el usuario debe confirmarlo

        # Re-mapear filas al estándar KusiDilve
        remapped_rows = []
        for row in rows:
            remapped = {}
            for kusi_field, user_header in current_mapping.items():
                remapped[kusi_field] = row.get(user_header, "")
            remapped_rows.append(remapped)

        # Limpia con el pipeline existente
        cleaned_rows, error_count = CSVCleaner.clean_csv(remapped_rows)

        # Guarda en BD
        for cleaned in cleaned_rows:
            book = Book(
                library_id=library_id,
                isbn13=cleaned.get("isbn13"),
                sku=cleaned.get("sku"),
                title=cleaned.get("title", ""),
                author=cleaned.get("author", ""),
                description=cleaned.get("description", ""),
                description_clean=cleaned.get("description_clean", ""),
                price=cleaned.get("price", 0.0),
                stock=cleaned.get("stock", 0),
                stock_status=cleaned.get("stock_status", "out_of_stock"),
                seo_title=cleaned.get("seo_title", ""),
                slug=cleaned.get("slug", ""),
                score_seo=cleaned.get("score_seo", 0),
                category_main=cleaned.get("categories", "Sin Categoría"),
                image_url=cleaned.get("images", ""),
                is_dirty=False,
                sync_date=datetime.utcnow()
            )
            db.add(book)

        library.books_count = len(cleaned_rows)
        library.last_sync = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "processed": len(rows),
            "cleaned": len(cleaned_rows),
            "errors": error_count,
            "suggested_mapping": current_mapping if not library.csv_mapping else None
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)