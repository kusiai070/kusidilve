# 🚀 KusiDilve - Quick Start (5 minutos)

## Paso 1: Instalación (2 min)

```bash
# Clonar/descargar proyecto
cd kusi-dilve-saas

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Paso 2: Configuración (1 min)

```bash
# Copiar configuración
cp .env.example .env

# Editar .env con tus credenciales (opcional para demo)
# DILVE_USER=tu_usuario
# WOOCOMMERCE_URL=https://mitienda.com
```

## Paso 3: Ejecutar Demo (1 min)

```bash
# Ver limpieza en acción
python demo.py
```

**Output esperado:**
```
🚀 KusiDilve - CSV Cleaner Demo
============================================================

📖 Leyendo CSV sucio...
✓ 10 libros cargados

🔴 ANTES (Sucio):
  Título: TÃ­tulo con UTF-8 roto
  Descripción: <p>DescripciÃ³n con HTML</p>...
  Stock: 5

✅ DESPUÉS (Limpio):
  Título: Título con UTF-8
  SEO Title: Título con UTF-8 | Autor Ejemplo
  Descripción: Descripción con HTML...
  Slug: titulo-con-utf-8-autor-ejemplo
  Stock Status: instock
  SEO Score: 85/100

📊 Estadísticas:
  Total de libros: 10
  Con stock: 7
  Sin stock: 3
  Score SEO promedio: 78.5/100
```

## Paso 4: Iniciar Servidor (1 min)

```bash
# Ejecutar FastAPI
uvicorn app:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

## Paso 5: Acceder al Dashboard

Abre en tu navegador:

- **Dashboard**: http://localhost:8000/templates/dashboard.html
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Funcionalidades Principales

### 1. Dashboard
- 📊 Métricas en tiempo real
- 📈 Gráficos interactivos
- 🧹 Estado de limpieza
- ⚡ Acciones rápidas

### 2. Sincronización
- 📤 Subir CSV DILVE
- 🔄 Sync automático desde DILVE
- 🛒 Sync a WooCommerce
- 👁️ Ocultar sin stock

### 3. Exportación
- 📥 Descargar CSV WooCommerce
- 📋 Formato estándar
- ✅ Listo para importar

### 4. Configuración
- 🔗 Conexiones DILVE/WooCommerce
- 💰 Gestión de planes
- ⚙️ Opciones avanzadas

## 📊 Datos de Prueba

El proyecto incluye 10 libros reales con problemas:

```csv
9788496479685,TÃ­tulo con UTF-8 roto,Autor Ejemplo,"<p>DescripciÃ³n con HTML</p>",18.95,5
9788496479686,Otro TÃ­tulo,Otro Autor,"Descripción normal",22.50,0
...
```

Después de limpiar:
- ✅ UTF-8 roto → Correcto
- ✅ HTML tags → Removidos
- ✅ Stock 0 → out_of_stock
- ✅ SEO optimizado

## 🔌 API Endpoints

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

## 🧪 Testing

### Test de Limpieza
```python
from csv_cleaner import CSVCleaner

row = {
    'titulo': 'TÃ­tulo',
    'descripcion': '<p>Texto</p>',
    'precio': '18.95',
    'stock': '5'
}

cleaned = CSVCleaner.clean_row(row)
print(cleaned['title'])  # Título
print(cleaned['stock_status'])  # instock
print(cleaned['score_seo'])  # 85
```

### Test de API
```bash
# Health check
curl http://localhost:8000/health

# Pricing
curl http://localhost:8000/pricing

# Docs
curl http://localhost:8000/docs
```

## 📁 Estructura

```
kusi-dilve-saas/
├── app.py                    # FastAPI principal
├── models.py                 # Schemas
├── database.py               # SQLAlchemy
├── csv_cleaner.py            # Limpieza
├── dilve_client.py           # DILVE API
├── woocommerce_sync.py       # WooCommerce
├── demo.py                   # Demo script
├── templates/
│   └── dashboard.html        # Dashboard
├── data/
│   └── mock_dilve_dirty.csv  # Datos mock
├── requirements.txt          # Dependencias
├── README.md                 # Documentación
├── API_DOCS.md               # API docs
└── QUICKSTART.md             # Este archivo
```

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements.txt
```

### Error: "Port 8000 already in use"
```bash
# Usar otro puerto
uvicorn app:app --reload --port 8001
```

### Error: "Database locked"
```bash
# Eliminar BD y recrear
rm kusi_dilve.db
uvicorn app:app --reload
```

### CSV no se procesa
- Verificar encoding UTF-8
- Verificar headers: isbn13, titulo, autor, descripcion, precio, stock
- Ver logs en consola

## 💡 Tips

1. **Datos Mock**: Usa `data/mock_dilve_dirty.csv` para testing
2. **Demo**: Ejecuta `python demo.py` para ver limpieza en acción
3. **Logs**: Revisa consola para ver detalles de sincronización
4. **API Docs**: Usa `/docs` para explorar endpoints interactivamente
5. **Dashboard**: Actualiza con botón 🔄 para ver cambios

## 🚀 Próximos Pasos

1. ✅ Instalar y ejecutar
2. ✅ Ver demo de limpieza
3. ✅ Explorar dashboard
4. ✅ Probar API endpoints
5. ⏭️ Conectar DILVE real
6. ⏭️ Conectar WooCommerce real
7. ⏭️ Configurar Stripe para pagos

## 📞 Soporte

- Docs: https://docs.kusidilve.com
- Issues: GitHub Issues
- Email: support@kusidilve.com

---

**¡Listo! 🎉 Tu SaaS está corriendo. Ahora a limpiar catálogos.**
