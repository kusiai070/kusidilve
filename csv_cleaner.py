"""
CSV Cleaner - Limpieza crítica de datos DILVE
UTF-8 roto, HTML tags, SEO optimization
"""
import re
import unicodedata
from typing import Dict, List
from bs4 import BeautifulSoup
from slugify import slugify
import logging
from thema_utils import map_thema_to_kusi

logger = logging.getLogger(__name__)


class CSVCleaner:
    """Limpia datos sucios de DILVE para WooCommerce"""

    @staticmethod
    def fix_utf8_encoding(text: str) -> str:
        """
        Arregla UTF-8 roto: Ã¡ → á, Ã± → ñ, etc.
        """
        if not text:
            return ""

        try:
            # Intenta decodificar como latin-1 y recodificar como UTF-8
            if isinstance(text, str):
                # Detecta patrones de UTF-8 roto
                text = text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Error fixing UTF-8: {e}")

        return text.strip()

    @staticmethod
    def strip_html_tags(text: str) -> str:
        """
        Elimina tags HTML y entidades HTML
        <p>Texto</p> → Texto
        &nbsp; → espacio
        """
        if not text:
            return ""

        try:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        except Exception as e:
            logger.warning(f"Error stripping HTML: {e}")
            # Fallback: regex simple
            text = re.sub(r'<[^>]+>', '', text)

        # Limpia espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def clean_description(text: str, max_length: int = 500) -> str:
        """
        Limpia descripción: UTF-8 + HTML + trunca
        """
        if not text:
            return ""

        # 1. Arregla UTF-8
        text = CSVCleaner.fix_utf8_encoding(text)

        # 2. Elimina HTML
        text = CSVCleaner.strip_html_tags(text)

        # 3. Limpia caracteres especiales
        text = re.sub(r'[^\w\s\-áéíóúñüÁÉÍÓÚÑÜ.,;:!?()]', '', text)

        # 4. Trunca
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

        return text.strip()

    @staticmethod
    def generate_seo_title(title: str, author: str = None, max_length: int = 60) -> str:
        """
        Genera SEO title: "Título | Autor"
        """
        if not title:
            return ""

        title = CSVCleaner.fix_utf8_encoding(title)
        title = CSVCleaner.strip_html_tags(title)

        if author:
            author = CSVCleaner.fix_utf8_encoding(author)
            seo_title = f"{title} | {author}"
        else:
            seo_title = title

        if len(seo_title) > max_length:
            seo_title = seo_title[:max_length].rsplit(' ', 1)[0]

        return seo_title.strip()

    @staticmethod
    def generate_meta_description(description: str, max_length: int = 155) -> str:
        """
        Genera meta description para SEO
        """
        if not description:
            return ""

        description = CSVCleaner.clean_description(description, max_length)
        return description[:max_length]

    @staticmethod
    def generate_slug(title: str, author: str = None) -> str:
        """
        Genera slug URL-friendly
        """
        if not title:
            return ""

        title = CSVCleaner.fix_utf8_encoding(title)
        title = CSVCleaner.strip_html_tags(title)

        if author:
            author = CSVCleaner.fix_utf8_encoding(author)
            slug_text = f"{title} {author}"
        else:
            slug_text = title

        return slugify(slug_text, max_length=100)

    @staticmethod
    def calculate_seo_score(book_data: Dict) -> int:
        """
        Calcula score SEO 0-100
        """
        score = 0

        # Title (20 puntos)
        if book_data.get('seo_title'):
            title_len = len(book_data['seo_title'])
            if 30 <= title_len <= 60:
                score += 20
            elif 20 <= title_len <= 70:
                score += 15
            else:
                score += 5

        # Description (20 puntos)
        if book_data.get('description_clean'):
            desc_len = len(book_data['description_clean'])
            if 100 <= desc_len <= 160:
                score += 20
            elif 50 <= desc_len <= 200:
                score += 15
            else:
                score += 5

        # Slug (15 puntos)
        if book_data.get('slug'):
            score += 15

        # Price (15 puntos)
        if book_data.get('price', 0) > 0:
            score += 15

        # Stock (15 puntos)
        if book_data.get('stock_status') == 'instock':
            score += 15

        # Author (10 puntos)
        if book_data.get('author'):
            score += 10

        return min(score, 100)

    @staticmethod
    def clean_row(row: Dict) -> Dict:
        """
        Limpia una fila completa de CSV DILVE
        """
        try:
            # Extrae campos
            isbn = row.get('isbn13', '').strip()
            title = row.get('titulo', row.get('title', '')).strip()
            author = row.get('autor', row.get('author', '')).strip()
            description = row.get('descripcion', row.get('description', '')).strip()
            price_str = row.get('precio', row.get('price', '0')).strip()
            stock_str = row.get('stock', '0').strip()

            # Limpia valores
            title = CSVCleaner.fix_utf8_encoding(title)
            title = CSVCleaner.strip_html_tags(title)

            author = CSVCleaner.fix_utf8_encoding(author)
            author = CSVCleaner.strip_html_tags(author)

            description_clean = CSVCleaner.clean_description(description)

            # Precio
            try:
                price = float(price_str.replace(',', '.')) if price_str else 0.0
            except ValueError:
                price = 0.0

            # Stock
            try:
                stock = int(stock_str) if stock_str else 0
            except ValueError:
                stock = 0

            stock_status = 'instock' if stock > 0 else 'out_of_stock'

            # SEO
            seo_title = CSVCleaner.generate_seo_title(title, author)
            slug = CSVCleaner.generate_slug(title, author)

            cleaned_row = {
                'isbn13': isbn,
                'sku': f"LIB-{isbn[-6:]}",  # SKU basado en últimos 6 dígitos ISBN
                'title': title,
                'author': author,
                'description': description,
                'description_clean': description_clean,
                'seo_title': seo_title,
                'slug': slug,
                'price': price,
                'stock': stock,
                'stock_status': stock_status,
                'manage_stock': True,
                'categories': map_thema_to_kusi(row.get('thema_code', row.get('materia_ibic', ''))),
                'images': row.get('images', ''),
            }

            # Calcula score SEO
            cleaned_row['score_seo'] = CSVCleaner.calculate_seo_score(cleaned_row)

            return cleaned_row

        except Exception as e:
            logger.error(f"Error cleaning row: {e}")
            return None

    @staticmethod
    def clean_csv(rows: List[Dict]) -> tuple[List[Dict], int]:
        """
        Limpia lista de filas CSV
        Retorna (cleaned_rows, error_count)
        """
        cleaned_rows = []
        error_count = 0

        for row in rows:
            cleaned = CSVCleaner.clean_row(row)
            if cleaned:
                cleaned_rows.append(cleaned)
            else:
                error_count += 1

        return cleaned_rows, error_count

    @staticmethod
    def to_woocommerce_csv(cleaned_rows: List[Dict]) -> str:
        """
        Convierte filas limpias a formato CSV WooCommerce Estándar
        Mapea campos KusiBook -> WooCommerce Product CSV Importer
        """
        if not cleaned_rows:
            return ""

        # Mapeo de headers KusiBook -> WooCommerce (campos oficiales)
        # WC Header: KusiBook Field
        wc_mapping = {
            'sku': 'sku',
            'name': 'post_title',
            'published': None,  # '1' por defecto
            'short_description': 'post_excerpt',
            'description': 'post_content',
            'regular_price': 'regular_price',
            'sale_price': 'sale_price',
            'stock_quantity': 'stock',
            'stock_status': 'stock_status',
            'manage_stock': None, # '1' por defecto
            'categories': 'category_main',
            'images': 'image_url',
            'slug': 'post_name',
            'meta:isbn13': 'isbn13',
            'meta:author': 'author',
            'meta:publisher': 'publisher',
            'meta:seo_title': 'seo_title',
            'meta:seo_description': 'seo_description'
        }

        headers = list(wc_mapping.keys())
        csv_lines = [','.join(headers)]

        for row in cleaned_rows:
            csv_values = []
            for header in headers:
                kusi_field = wc_mapping[header]
                val = ""
                
                if kusi_field is None:
                    if header in ['published', 'manage_stock']:
                        val = '1'
                else:
                    val = row.get(kusi_field, "")
                    if val is None: val = ""
                
                # Escapado simple de comas para CSV
                str_val = str(val).replace('"', '""')
                csv_values.append(f'"{str_val}"')
            
            csv_lines.append(','.join(csv_values))

        return '\n'.join(csv_lines)
