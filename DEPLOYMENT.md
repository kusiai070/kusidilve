# KusiDilve - Deployment Guide

## 🚀 Deployment a Producción

### Opción 1: Heroku (Recomendado para MVP)

#### 1. Preparar proyecto

```bash
# Crear Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port \$PORT" > Procfile

# Crear runtime.txt
echo "python-3.11.7" > runtime.txt

# Crear .gitignore
echo "venv/
*.db
.env
__pycache__/
.DS_Store" > .gitignore

# Inicializar git
git init
git add .
git commit -m "Initial commit: KusiDilve SaaS MVP"
```

#### 2. Desplegar a Heroku

```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Crear app
heroku create kusidilve-saas

# Configurar variables de entorno
heroku config:set DILVE_USER=tu_usuario
heroku config:set DILVE_PASSWORD=tu_password
heroku config:set WOOCOMMERCE_URL=https://mitienda.com
heroku config:set WOOCOMMERCE_KEY=ck_xxxxx
heroku config:set WOOCOMMERCE_SECRET=cs_xxxxx
heroku config:set STRIPE_SECRET_KEY=sk_test_xxxxx

# Desplegar
git push heroku main

# Ver logs
heroku logs --tail
```

### Opción 2: Docker (Recomendado para escalabilidad)

#### 1. Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio de datos
RUN mkdir -p data

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Crear docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./kusi_dilve.db
      - DILVE_USER=${DILVE_USER}
      - DILVE_PASSWORD=${DILVE_PASSWORD}
      - WOOCOMMERCE_URL=${WOOCOMMERCE_URL}
      - WOOCOMMERCE_KEY=${WOOCOMMERCE_KEY}
      - WOOCOMMERCE_SECRET=${WOOCOMMERCE_SECRET}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  celery:
    build: .
    command: celery -A app worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///./kusi_dilve.db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped
```

#### 3. Ejecutar con Docker

```bash
# Build
docker build -t kusidilve .

# Run
docker run -p 8000:8000 kusidilve

# O con docker-compose
docker-compose up -d
```

### Opción 3: AWS (Recomendado para producción)

#### 1. Usar AWS Elastic Beanstalk

```bash
# Instalar EB CLI
pip install awsebcli

# Inicializar
eb init -p python-3.11 kusidilve

# Crear entorno
eb create kusidilve-prod

# Desplegar
eb deploy

# Ver logs
eb logs
```

#### 2. Configurar RDS (PostgreSQL)

```bash
# En AWS Console:
# 1. Crear RDS PostgreSQL instance
# 2. Copiar connection string
# 3. Actualizar DATABASE_URL en .env

# Actualizar models para PostgreSQL
# En database.py:
# DATABASE_URL = "postgresql://user:password@host:5432/kusidilve"
```

### Opción 4: DigitalOcean App Platform

```bash
# 1. Conectar GitHub
# 2. Seleccionar repositorio
# 3. Configurar:
#    - Build command: pip install -r requirements.txt
#    - Run command: uvicorn app:app --host 0.0.0.0 --port 8080
# 4. Agregar variables de entorno
# 5. Deploy
```

## 🔒 Seguridad en Producción

### 1. Encriptar Credenciales

```python
# En database.py, usar cryptography
from cryptography.fernet import Fernet

# Generar key
key = Fernet.generate_key()
cipher = Fernet(key)

# Encriptar
encrypted = cipher.encrypt(b"password")

# Desencriptar
decrypted = cipher.decrypt(encrypted)
```

### 2. HTTPS Obligatorio

```python
# En app.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["kusidilve.com", "www.kusidilve.com"]
)
```

### 3. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/sync/dilve/{library_id}")
@limiter.limit("5/minute")
async def sync_dilve(...):
    ...
```

### 4. JWT Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401)
    return user_id
```

## 📊 Monitoreo

### 1. Logging

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
logging.getLogger().addHandler(handler)
```

### 2. Sentry (Error Tracking)

```bash
pip install sentry-sdk

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://xxxxx@sentry.io/xxxxx",
    integrations=[FastApiIntegration()]
)
```

### 3. Prometheus (Metrics)

```bash
pip install prometheus-client

from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

## 🗄️ Base de Datos

### Migración a PostgreSQL

```bash
# Instalar alembic
pip install alembic

# Inicializar
alembic init migrations

# Crear migración
alembic revision --autogenerate -m "Initial migration"

# Aplicar
alembic upgrade head
```

### Backup Automático

```bash
# Script de backup
#!/bin/bash
BACKUP_DIR="/backups"
DB_FILE="kusi_dilve.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cp $DB_FILE $BACKUP_DIR/kusi_dilve_$TIMESTAMP.db
gzip $BACKUP_DIR/kusi_dilve_$TIMESTAMP.db

# Cron job (cada día a las 2 AM)
0 2 * * * /path/to/backup.sh
```

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: kusidilve-saas
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

## 📈 Escalabilidad

### 1. Caché con Redis

```python
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/api/dashboard/{library_id}")
async def get_dashboard(library_id: int):
    # Intentar obtener del caché
    cached = cache.get(f"dashboard:{library_id}")
    if cached:
        return json.loads(cached)
    
    # Si no está en caché, calcular
    data = calculate_dashboard(library_id)
    
    # Guardar en caché por 5 minutos
    cache.setex(f"dashboard:{library_id}", 300, json.dumps(data))
    
    return data
```

### 2. Celery para Background Tasks

```python
from celery import Celery

celery_app = Celery('kusidilve', broker='redis://localhost:6379')

@celery_app.task
def sync_dilve_task(library_id: int, from_date: str):
    # Sincronización en background
    dilve_sync = DilveSync(...)
    result = await dilve_sync.sync_from_date(from_date)
    return result

# En app.py
@app.post("/api/sync/dilve/{library_id}")
async def sync_dilve(library_id: int):
    sync_dilve_task.delay(library_id, "2025-12-22")
    return {"status": "processing"}
```

### 3. Load Balancing

```bash
# nginx.conf
upstream kusidilve {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name kusidilve.com;

    location / {
        proxy_pass http://kusidilve;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📋 Checklist de Deployment

- [ ] Configurar variables de entorno
- [ ] Encriptar credenciales
- [ ] Habilitar HTTPS
- [ ] Configurar CORS
- [ ] Implementar JWT
- [ ] Agregar rate limiting
- [ ] Configurar logging
- [ ] Configurar Sentry
- [ ] Configurar backups
- [ ] Configurar CI/CD
- [ ] Configurar monitoreo
- [ ] Configurar alertas
- [ ] Documentar deployment
- [ ] Crear runbook
- [ ] Entrenar equipo

## 🆘 Troubleshooting

### Error: "Connection refused"
```bash
# Verificar que el servidor está corriendo
curl http://localhost:8000/health
```

### Error: "Database locked"
```bash
# Usar PostgreSQL en lugar de SQLite
# Actualizar DATABASE_URL
```

### Error: "Out of memory"
```bash
# Aumentar recursos
# Implementar caché
# Optimizar queries
```

---

**Deployment ready! 🚀**
