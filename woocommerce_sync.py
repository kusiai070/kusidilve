"""
WooCommerce Sync - Gestor de sincronización de stock
"""
import httpx
import logging
from typing import Dict, List, Optional
from base64 import b64encode
import json

logger = logging.getLogger(__name__)


class WooCommerceClient:
    """Cliente para API REST WooCommerce"""

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        """
        Args:
            store_url: URL de la tienda (ej: https://mitienda.com)
            consumer_key: Clave de consumidor WooCommerce
            consumer_secret: Secreto de consumidor WooCommerce
        """
        self.store_url = store_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.store_url}/wp-json/wc/v3"
        self.timeout = 30

    def _get_auth_header(self) -> Dict:
        """Genera header de autenticación Basic Auth"""
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded = b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    async def test_connection(self) -> Dict:
        """
        Prueba conexión a WooCommerce
        """
        try:
            url = f"{self.api_url}/products?per_page=1"
            headers = self._get_auth_header()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                logger.info("WooCommerce connection successful")
                return {
                    "status": "success",
                    "message": "Conexión exitosa a WooCommerce"
                }

        except Exception as e:
            logger.error(f"WooCommerce connection error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Obtiene producto por SKU
        """
        try:
            url = f"{self.api_url}/products"
            params = {"sku": sku}
            headers = self._get_auth_header()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                products = response.json()
                if products:
                    return products[0]
                return None

        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            return None

    async def create_product(self, product_data: Dict) -> Optional[Dict]:
        """
        Crea nuevo producto en WooCommerce
        """
        try:
            url = f"{self.api_url}/products"
            headers = self._get_auth_header()
            headers["Content-Type"] = "application/json"

            payload = {
                "name": product_data.get("title"),
                "sku": product_data.get("sku"),
                "description": product_data.get("description_clean"),
                "short_description": product_data.get("description_clean", "")[:155],
                "regular_price": str(product_data.get("price", 0)),
                "stock_quantity": product_data.get("stock", 0),
                "stock_status": product_data.get("stock_status", "out_of_stock"),
                "manage_stock": True,
                "categories": [{"name": product_data.get("categories", "Ficción")}],
                "meta_data": [
                    {"key": "isbn13", "value": product_data.get("isbn13")},
                    {"key": "author", "value": product_data.get("author", "")},
                    {"key": "seo_score", "value": str(product_data.get("score_seo", 0))}
                ]
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                product = response.json()
                logger.info(f"Product created: {product.get('id')} - {product.get('name')}")
                return product

        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return None

    async def update_product(self, product_id: int, product_data: Dict) -> Optional[Dict]:
        """
        Actualiza producto existente
        """
        try:
            url = f"{self.api_url}/products/{product_id}"
            headers = self._get_auth_header()
            headers["Content-Type"] = "application/json"

            payload = {
                "name": product_data.get("title"),
                "description": product_data.get("description_clean"),
                "short_description": product_data.get("description_clean", "")[:155],
                "regular_price": str(product_data.get("price", 0)),
                "stock_quantity": product_data.get("stock", 0),
                "stock_status": product_data.get("stock_status", "out_of_stock"),
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()

                product = response.json()
                logger.info(f"Product updated: {product_id}")
                return product

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            return None

    async def update_stock(self, product_id: int, stock: int, status: str = None) -> Optional[Dict]:
        """
        Actualiza stock de producto
        """
        try:
            url = f"{self.api_url}/products/{product_id}"
            headers = self._get_auth_header()
            headers["Content-Type"] = "application/json"

            payload = {
                "stock_quantity": stock,
            }

            if status:
                payload["stock_status"] = status

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()

                product = response.json()
                logger.info(f"Stock updated: {product_id} -> {stock}")
                return product

        except Exception as e:
            logger.error(f"Error updating stock for {product_id}: {e}")
            return None

    async def hide_out_of_stock(self, product_id: int) -> Optional[Dict]:
        """
        Oculta producto sin stock
        """
        try:
            url = f"{self.api_url}/products/{product_id}"
            headers = self._get_auth_header()
            headers["Content-Type"] = "application/json"

            payload = {
                "status": "draft",  # Oculta del catálogo
                "stock_status": "out_of_stock"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()

                logger.info(f"Product hidden: {product_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Error hiding product {product_id}: {e}")
            return None

    async def get_all_products(self, per_page: int = 100) -> List[Dict]:
        """
        Obtiene todos los productos (paginado)
        """
        try:
            all_products = []
            page = 1

            while True:
                url = f"{self.api_url}/products"
                params = {"per_page": per_page, "page": page}
                headers = self._get_auth_header()

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()

                    products = response.json()
                    if not products:
                        break

                    all_products.extend(products)
                    page += 1

            logger.info(f"Retrieved {len(all_products)} products from WooCommerce")
            return all_products

        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []


class WooCommerceSync:
    """Gestor de sincronización WooCommerce"""

    def __init__(self, wc_client: WooCommerceClient):
        self.wc = wc_client

    async def sync_products(self, cleaned_books: List[Dict]) -> Dict:
        """
        Sincroniza libros limpios a WooCommerce
        
        Returns:
            {
                "status": "success",
                "created": 10,
                "updated": 5,
                "errors": 2,
                "total": 17
            }
        """
        created = 0
        updated = 0
        errors = 0

        for book in cleaned_books:
            try:
                # Busca producto existente por SKU
                existing = await self.wc.get_product_by_sku(book["sku"])

                if existing:
                    # Actualiza
                    result = await self.wc.update_product(existing["id"], book)
                    if result:
                        updated += 1
                    else:
                        errors += 1
                else:
                    # Crea nuevo
                    result = await self.wc.create_product(book)
                    if result:
                        created += 1
                    else:
                        errors += 1

            except Exception as e:
                logger.error(f"Error syncing product {book.get('sku')}: {e}")
                errors += 1

        return {
            "status": "success" if errors == 0 else "partial",
            "created": created,
            "updated": updated,
            "errors": errors,
            "total": len(cleaned_books)
        }

    async def hide_out_of_stock_products(self) -> Dict:
        """
        Oculta todos los productos sin stock
        """
        try:
            products = await self.wc.get_all_products()
            hidden = 0
            errors = 0

            for product in products:
                if product.get("stock_status") == "out_of_stock":
                    result = await self.wc.hide_out_of_stock(product["id"])
                    if result:
                        hidden += 1
                    else:
                        errors += 1

            return {
                "status": "success" if errors == 0 else "partial",
                "hidden": hidden,
                "errors": errors,
                "total": len(products)
            }

        except Exception as e:
            logger.error(f"Error hiding out of stock products: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def sync_stock_only(self, books: List[Dict]) -> Dict:
        """
        Sincroniza solo stock (sin actualizar otros campos)
        """
        updated = 0
        errors = 0

        for book in books:
            try:
                existing = await self.wc.get_product_by_sku(book["sku"])
                if existing:
                    result = await self.wc.update_stock(
                        existing["id"],
                        book["stock"],
                        book["stock_status"]
                    )
                    if result:
                        updated += 1
                    else:
                        errors += 1

            except Exception as e:
                logger.error(f"Error updating stock for {book.get('sku')}: {e}")
                errors += 1

        return {
            "status": "success" if errors == 0 else "partial",
            "updated": updated,
            "errors": errors,
            "total": len(books)
        }
