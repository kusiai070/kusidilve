# 🚀 KusiDilve SaaS - MVP Completo

**Limpieza DILVE → WooCommerce Sync para librerías españolas**

## 📋 Descripción

KusiDilve es una plataforma SaaS que automatiza la limpieza de catálogos DILVE sucios y los sincroniza con WooCommerce. Transforma datos con UTF-8 roto, HTML tags y problemas de stock en CSVs perfectos listos para vender.

### ✨ Características Principales

- **🧹 Limpieza Inteligente**: UTF-8 roto (Ã¡→á), HTML tags, caracteres especiales
- **📊 Dashboard Moderno**: Métricas en tiempo real, gráficos interactivos
- **🔄 Sync Automático**: DILVE → WooCommerce con un clic
- **📈 SEO Optimizado**: Títulos, descripciones, slugs perfectos
- **💰 Planes Flexibles**: Básico (€9), PRO (€29), Premium (€59)
- **📁 Exportación**: CSV WooCommerce listo para importar
- **⚡ Stock Manager**: Oculta productos sin stock automáticamente

## 🛠️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: HTML5 + HTMX + TailwindCSS + Chart.js
- **Limpieza**: BeautifulSoup4 + python-slugify
- **APIs**: DILVE REST + WooCommerce REST
- **Pagos**: Stripe (integrado)
- **Async**: asyncio + httpx

## 📁 Estructura del Proyecto

```
kusi-dilve-saas/
├── app.py                    # FastAPI principal
├── models.py                 # Pydantic schemas
├── database.py               # SQLAlchemy + SQLite
├── csv_cleaner.py            # Limpieza UTF-8/HTML/SEO
├── dilve_client.py           # Cliente DILVE API
├── woocommerce_sync.py       # Sync WooCommerce
├── requirements.txt          # Dependencias
├── .env.example              # Configuración
├── templates/
│   └── dashboard.html        # Dashboard principal
├── data/
│   ├── mock_dilve_dirty.csv  # Datos mock sucios
│   └── mock_dilve_clean.csv  # Referencia limpia
└── README.md                 # Este archivo
```

## 🚀 Instalación Rápida

### 1. Clonar/Descargar

```bash
cd kusi-dilve-saas
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales DILVE y WooCommerce
```

### 5. Ejecutar servidor

```bash
uvicorn app:app --reload
```

El servidor estará disponible en: **http://localhost:8000**

- Dashboard: http://localhost:8000/templates/dashboard.html
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 API Endpoints

### Librerías

```
POST   /api/libraries              # Crear librería
GET    /api/libraries/{id}         # Obtener librería
```

### Dashboard

```
GET    /api/dashboard/{library_id} # Métricas dashboard
```

### Sincronización

```
POST   /api/sync/dilve/{library_id}        # Sync desde DILVE
POST   /api/sync/woocommerce/{library_id}  # Sync a WooCommerce
POST   /api/upload/csv/{library_id}        # Subir CSV
```

### Exportación

```
GET    /api/export/woocommerce/{library_id}  # Descargar CSV WooCommerce
```

### Públicos

```
GET    /pricing                    # Planes de precios
GET    /health                     # Health check
```

## 🧹 Limpieza de Datos

### Problemas que resuelve

| Problema | Entrada | Salida |
|----------|---------|--------|
| UTF-8 roto | `TÃ­tulo` | `Título` |
| HTML tags | `<p>Texto</p>` | `Texto` |
| Espacios múltiples | `Texto  con   espacios` | `Texto con espacios` |
| Caracteres especiales | `&nbsp;&nbsp;` | ` ` |
| Stock 0 | `stock: 0` | `stock_status: out_of_stock` |

### Ejemplo de limpieza

```python
from csv_cleaner import CSVCleaner

row = {
    'titulo': 'TÃ­tulo con UTF-8',
    'descripcion': '<p>DescripciÃ³n</p>',
    'precio': '18.95',
    'stock': '5'
}

cleaned = CSVCleaner.clean_row(row)
# Resultado:
# {
#     'title': 'Título con UTF-8',
#     'description_clean': 'Descripción',
#     'seo_title': 'Título con UTF-8 | Autor',
#     'slug': 'titulo-con-utf-8-autor',
#     'price': 18.95,
#     'stock_status': 'instock',
#     'score_seo': 85
# }
```

## 💰 Planes de Precios

### Básico - €9/mes
- CSV limpio mensual
- Hasta 5.000 libros
- Soporte por email
- Limpieza UTF-8/HTML

### PRO - €29/mes ⭐
- Todo Básico +
- **Sync stock automático**
- Hasta 50.000 libros
- Soporte prioritario
- API REST acceso

### Premium - €59/mes
- Todo PRO +
- Alertas en tiempo real
- Sincronización cada hora
- Hasta 500.000 libros
- Soporte 24/7
- Consultoría SEO

## 🔌 Integración DILVE

### Endpoints DILVE utilizados

```
GET /dilve/getRecordStatusX.do
    - Obtiene cambios desde fecha
    - Parámetros: user, password, fromDate, type

GET /dilve/getRecordsX.do
    - Obtiene registros por ISBN (máx 128)
    - Parámetros: identifier, metadataformat, user, password

FTP ftp.dilve.es/extracciones/
    - Descargas de catálogos completos
```

### Autenticación

```python
dilve_client = DilveClient(user="tu_usuario", password="tu_password")
result = await dilve_client.get_record_status(from_date="2025-12-22")
```

## 🛒 Integración WooCommerce

### Autenticación

```python
wc_client = WooCommerceClient(
    store_url="https://mitienda.com",
    consumer_key="ck_xxxxx",
    consumer_secret="cs_xxxxx"
)
```

### Operaciones

```python
# Crear producto
await wc_client.create_product(product_data)

# Actualizar stock
await wc_client.update_stock(product_id, stock=10)

# Ocultar sin stock
await wc_client.hide_out_of_stock(product_id)
```

## 📊 Base de Datos

### Tablas

```sql
-- Librerías
CREATE TABLE libraries (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE,
    dilve_user VARCHAR,
    woocommerce_url VARCHAR,
    plan VARCHAR DEFAULT 'basic',
    books_count INTEGER DEFAULT 0,
    last_sync DATETIME
);

-- Libros
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    library_id INTEGER FOREIGN KEY,
    isbn13 VARCHAR,
    title VARCHAR,
    description_clean TEXT,
    seo_title VARCHAR,
    slug VARCHAR,
    price FLOAT,
    stock INTEGER,
    stock_status VARCHAR,
    score_seo INTEGER,
    is_dirty BOOLEAN,
    sync_date DATETIME
);

-- Logs de sincronización
CREATE TABLE sync_logs (
    id INTEGER PRIMARY KEY,
    library_id INTEGER FOREIGN KEY,
    processed INTEGER,
    cleaned INTEGER,
    errors INTEGER,
    duration_seconds FLOAT,
    status VARCHAR,
    created_at DATETIME
);
```

## 📋 Módulo WP All Import (⭐ EXCLUSIVO)

KusiDilve incluye un **módulo especializado para WordPress** que convierte datos DILVE sucios a formato **WP All Import Step 4** (drag&drop).

### Características

- ✅ Conversión exacta a campos WordPress
- ✅ Limpieza UTF-8 + HTML automática
- ✅ Generación de slugs WordPress-compatible
- ✅ SEO titles optimizados
- ✅ Estadísticas de importación
- ✅ Reporte automático

### Archivo Principal

**`csv_wpallimport.py`** (500+ líneas)

```python
from csv_wpallimport import WPAllImportConverter, WPAllImportStats

# Convertir fila DILVE a WP All Import
cleaned = WPAllImportConverter.dilve_to_wp_all_import(dilve_row)

# Procesar CSV completo
result = WPAllImportConverter.process_dilve_csv(
    'input.csv',
    'output_wp_all_import.csv'
)

# Generar estadísticas
stats = WPAllImportStats.analyze_wp_import(wp_rows)
report = WPAllImportStats.generate_import_report(wp_rows)
```

### Campos Mapeados

| DILVE | WP All Import |
|-------|---------------|
| `titulo` | `post_title` (SEO optimizado) |
| `descripcion` | `post_content` + `post_excerpt` |
| `isbn13` | `_id` (identificador único) |
| `precio` | `_regular_price` |
| `stock` | `_stock` + `post_status` |
| `autor` | Incluido en `post_title` |

### Ejemplo de Conversión

**ANTES (DILVE sucio):**
```json
{
  "titulo": "TÃ­tulo con UTF-8 roto",
  "descripcion": "<p>DescripciÃ³n con HTML</p>",
  "precio": "18.95",
  "stock": "5"
}
```

**DESPUÉS (WP All Import perfecto):**
```json
{
  "_id": "9788496479685",
  "post_title": "Título con UTF-8 roto | Autor",
  "post_content": "Descripción con HTML",
  "post_excerpt": "Descripción con HTML...",
  "_sku": "LIB479685",
  "_regular_price": "18.95",
  "_stock": "5",
  "post_status": "publish",
  "post_name": "titulo-con-utf-8-roto-autor"
}
```

### Uso en Dashboard

1. Ve a **Exportar** → **WP All Import**
2. Haz clic en **"Descargar CSV"**
3. Archivo: `wp_all_import_ready.csv`

### Uso en API

```bash
# Descargar CSV WP All Import
curl http://localhost:8000/api/export/wp-all-import/1 \
  -o wp_all_import_ready.csv
```

### Importar en WordPress

1. Instala **WP All Import** plugin
2. Crea nuevo import
3. Sube el CSV descargado
4. **Step 1:** Selecciona archivo
5. **Step 2:** Configura delimitador (coma)
6. **Step 3:** Mapea campos (ya están listos)
7. **Step 4:** Revisa preview
8. **¡Importa!**

### Estadísticas Incluidas

```python
stats = {
    'total_products': 100,
    'instock': 75,
    'out_of_stock': 25,
    'percentage_instock': 75.0,
    'categories': {'Ficción': 45, 'No Ficción': 55},
    'avg_price': 19.95,
    'min_price': 9.99,
    'max_price': 49.99,
    'total_value': 1995.00
}
```

### Reporte de Importación

Genera reporte automático con:
- Estadísticas generales
- Análisis de precios
- Desglose por categorías
- Instrucciones paso a paso

---

## 🧪 Testing

### Datos Mock

El proyecto incluye `data/mock_dilve_dirty.csv` con 10 libros reales con problemas:

```csv
isbn13,titulo,autor,descripcion,precio,stock
9788496479685,TÃ­tulo con UTF-8 roto,Autor Ejemplo,"<p>DescripciÃ³n con HTML</p>",18.95,5
...
```

### Probar limpieza

```bash
python -c "
from csv_cleaner import CSVCleaner
import csv

with open('data/mock_dilve_dirty.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    cleaned, errors = CSVCleaner.clean_csv(rows)
    print(f'Limpios: {len(cleaned)}, Errores: {errors}')
    print(cleaned[0])
"
```

### Ejecutar Pruebas Unitarias

El proyecto incluye una suite de tests para validar la lógica de limpieza y mapeo.

```bash
# Ejecutar todos los tests
python -m unittest discover tests

# Ejecutar un test específico
python -m unittest tests/test_thema_utils.py
```

## 🔐 Seguridad

### TODO en Producción

- [ ] Encriptar credenciales DILVE/WooCommerce en BD
- [ ] Usar JWT para autenticación API
- [ ] HTTPS obligatorio
- [ ] Rate limiting en endpoints
- [ ] Validación de CORS
- [ ] Logs de auditoría
- [ ] Backup automático de BD

## 📈 Roadmap

### v1.1
- [ ] Autenticación con JWT
- [ ] Dashboard multi-usuario
- [ ] Webhooks para eventos
- [ ] Notificaciones por email

### v1.2
- [ ] Integración con más plataformas (Shopify, Magento)
- [ ] Análisis de competencia
- [ ] Recomendaciones de precios

### v2.0
- [ ] App móvil
- [ ] IA para optimización de descripciones
- [ ] Marketplace integrado

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

- Email: support@kusidilve.com
- Docs: https://docs.kusidilve.com
- Issues: GitHub Issues

## 🙏 Agradecimientos

- DILVE por la API de catálogos
- WooCommerce por la plataforma
- FastAPI por el framework
- La comunidad open source

---

**Hecho con ❤️ para librerías españolas**

*KusiDilve - Limpieza DILVE → WooCommerce Sync*
