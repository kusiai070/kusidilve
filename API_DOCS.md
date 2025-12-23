# KusiDilve API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

Actualmente sin autenticación (TODO: Implementar JWT en v1.1)

## Endpoints

### 1. Librerías

#### Crear Librería

```http
POST /libraries
Content-Type: application/json

{
  "name": "Librería Central",
  "email": "info@libreria.com",
  "dilve_user": "usuario_dilve",
  "dilve_password": "password_dilve",
  "woocommerce_url": "https://mitienda.com",
  "woocommerce_key": "ck_xxxxx",
  "woocommerce_secret": "cs_xxxxx"
}
```

**Response (201)**
```json
{
  "id": 1,
  "name": "Librería Central",
  "email": "info@libreria.com",
  "plan": "basic",
  "books_count": 0,
  "created_at": "2025-12-23T10:30:00",
  "last_sync": null
}
```

#### Obtener Librería

```http
GET /libraries/{library_id}
```

**Response (200)**
```json
{
  "id": 1,
  "name": "Librería Central",
  "email": "info@libreria.com",
  "plan": "pro",
  "books_count": 8127,
  "created_at": "2025-12-23T10:30:00",
  "last_sync": "2025-12-23T15:45:00"
}
```

---

### 2. Dashboard

#### Obtener Métricas

```http
GET /dashboard/{library_id}
```

**Response (200)**
```json
{
  "total_books": 8127,
  "active_books": 3235,
  "out_of_stock": 4892,
  "dirty_count": 1200,
  "clean_count": 6927,
  "seo_score": 67.5,
  "last_sync": "2025-12-23T15:45:00",
  "plan": "pro",
  "percentage_clean": 85.2
}
```

**Campos**
- `total_books`: Total de libros en catálogo
- `active_books`: Libros con stock > 0
- `out_of_stock`: Libros sin stock
- `dirty_count`: Libros sin limpiar
- `clean_count`: Libros limpios
- `seo_score`: Score SEO promedio (0-100)
- `percentage_clean`: Porcentaje de libros limpios

---

### 3. Sincronización DILVE

#### Sincronizar desde DILVE

```http
POST /sync/dilve/{library_id}
Content-Type: application/json

{
  "from_date": "2025-12-22",
  "type": "A"
}
```

**Parámetros**
- `from_date`: Fecha en formato YYYY-MM-DD (opcional, default: 2025-12-22)
- `type`: Tipo de cambios (opcional)
  - `A`: Todos (default)
  - `N`: Nuevos
  - `M`: Modificados
  - `D`: Eliminados

**Response (202)**
```json
{
  "status": "processing",
  "message": "Sincronización iniciada",
  "library_id": 1
}
```

**Nota**: La sincronización se ejecuta en background. Usa GET /dashboard para ver progreso.

---

### 4. Sincronización WooCommerce

#### Sincronizar a WooCommerce

```http
POST /sync/woocommerce/{library_id}
```

**Response (202)**
```json
{
  "status": "processing",
  "message": "Sincronización WooCommerce iniciada",
  "library_id": 1
}
```

**Requisitos**
- Plan: PRO o Premium (no disponible en Básico)
- Credenciales WooCommerce configuradas

**Operaciones**
- Crea productos nuevos
- Actualiza productos existentes
- Sincroniza stock
- Actualiza descripciones y SEO

---

### 5. Upload CSV

#### Subir y Procesar CSV

```http
POST /upload/csv/{library_id}
Content-Type: multipart/form-data

file: <archivo.csv>
```

**CSV Esperado**
```csv
isbn13,titulo,autor,descripcion,precio,stock
9788496479685,Título,Autor,"Descripción",18.95,5
```

**Response (200)**
```json
{
  "status": "success",
  "processed": 100,
  "cleaned": 98,
  "errors": 2
}
```

**Campos**
- `processed`: Total de filas procesadas
- `cleaned`: Filas limpias exitosamente
- `errors`: Filas con errores

---

### 6. Exportación

#### Exportar CSV WooCommerce

```http
GET /export/woocommerce/{library_id}
```

**Response (200)**
- Content-Type: `text/csv`
- Descarga archivo: `woocommerce_export.csv`

**Formato CSV**
```csv
id,type,sku,name,published,is_featured,visibility,short_description,description,date_on_sale_from,date_on_sale_to,sale_price,regular_price,weight,length,width,height,categories,tags,shipping_class,images,download_limit,download_expiry,parent_id,grouped_products,upsell_ids,cross_sell_ids,external_url,button_text,position,attribute_pa_color,attribute_pa_size,meta:_custom_field,stock_status,manage_stock,stock_quantity
1,simple,LIB-479685,"Título","1","0","visible","Descripción","Descripción","","","","18.95","","","","","Ficción","","","","","","","","","","","","","","","","instock","1","5"
```

---

### 7. Precios

#### Obtener Planes

```http
GET /pricing
```

**Response (200)**
```json
{
  "plans": [
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
}
```

---

### 8. Health Check

#### Verificar Estado

```http
GET /health
```

**Response (200)**
```json
{
  "status": "ok",
  "timestamp": "2025-12-23T16:30:00.123456"
}
```

---

## Error Handling

### Errores Comunes

#### 404 - No Encontrado

```json
{
  "detail": "Librería no encontrada"
}
```

#### 400 - Solicitud Inválida

```json
{
  "detail": "Email ya registrado"
}
```

#### 403 - Prohibido

```json
{
  "detail": "Plan Básico no incluye sync WooCommerce"
}
```

#### 500 - Error Interno

```json
{
  "detail": "Error al procesar solicitud"
}
```

---

## Rate Limiting

Actualmente sin límite de rate (TODO: Implementar en producción)

---

## Ejemplos cURL

### Crear Librería

```bash
curl -X POST http://localhost:8000/api/libraries \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Librería",
    "email": "info@milib.com",
    "dilve_user": "usuario",
    "dilve_password": "password",
    "woocommerce_url": "https://mitienda.com",
    "woocommerce_key": "ck_xxxxx",
    "woocommerce_secret": "cs_xxxxx"
  }'
```

### Obtener Dashboard

```bash
curl http://localhost:8000/api/dashboard/1
```

### Sincronizar DILVE

```bash
curl -X POST http://localhost:8000/api/sync/dilve/1 \
  -H "Content-Type: application/json" \
  -d '{
    "from_date": "2025-12-22"
  }'
```

### Subir CSV

```bash
curl -X POST http://localhost:8000/api/upload/csv/1 \
  -F "file=@datos.csv"
```

### Exportar WooCommerce

```bash
curl http://localhost:8000/api/export/woocommerce/1 \
  -o woocommerce_export.csv
```

---

## Webhooks (TODO)

Próximamente:
- `library.created`
- `sync.completed`
- `sync.failed`
- `subscription.updated`

---

## Versioning

API Version: **v1.0.0**

Cambios futuros serán versionados como `/api/v2/...`

---

## Soporte

Para preguntas o problemas:
- Email: support@kusidilve.com
- Docs: https://docs.kusidilve.com
- Issues: GitHub Issues
