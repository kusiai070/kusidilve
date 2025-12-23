"""
WP All Import Module - Exportación optimizada para WordPress
Convierte DILVE → WP All Import Step 4 (drag&drop ready)
"""
import csv
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Campos exactos que WP All Import espera en Step 4
WP_ALL_IMPORT_FIELDS = [
    '_id', 'post_title', 'post_content', 'post_excerpt', '_sku',
    '_regular_price', '_sale_price', '_stock', '_manage_stock',
    '_virtual', '_downloadable', 'product_cat', 'tax_status',
    'post_status', 'post_name', 'images', 'post_parent', 'menu_order',
    '_weight', '_length', '_width', '_height', '_shipping_class',
    'attribute_pa_color', 'attribute_pa_size', 'attribute_pa_material'
]


class WPAllImportConverter:
    """Convierte datos DILVE a formato WP All Import"""

    @staticmethod
    def clean_dilve_text(text: str, max_length: int = 1600) -> str:
        """
        Limpia UTF-8 roto + HTML para WP All Import
        
        Problemas que resuelve:
        - Ã¡ → á, Ã± → ñ (UTF-8 roto)
        - <p>, <b>, <i> → removidos
        - &nbsp; → espacio
        - Caracteres especiales → removidos
        """
        if not text:
            return ""

        try:
            # 1. Intenta decodificar UTF-8 roto
            if isinstance(text, str):
                try:
                    text = text.encode('latin1').decode('utf-8', errors='replace')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass

            # 2. Elimina HTML tags
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            # 3. Limpia caracteres especiales (mantiene acentos españoles)
            text = re.sub(
                r'[^\w\sáéíóúñÁÉÍÓÚÑ\-.,;:!?¿¡\(\)]',
                '',
                text
            )

            # 4. Limpia espacios múltiples
            text = ' '.join(text.split())

            # 5. Trunca si es necesario
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + '...'

            return text.strip()

        except Exception as e:
            logger.warning(f"Error cleaning text: {e}")
            return text[:max_length] if text else ""

    @staticmethod
    def generate_wp_slug(title: str, author: str = None) -> str:
        """
        Genera slug compatible con WordPress
        Ejemplo: "El Quijote de Cervantes" → "el-quijote-de-cervantes"
        """
        if not title:
            return ""

        # Limpia primero
        title = WPAllImportConverter.clean_dilve_text(title)

        if author:
            author = WPAllImportConverter.clean_dilve_text(author)
            slug_text = f"{title} {author}"
        else:
            slug_text = title

        # Convierte a minúsculas
        slug = slug_text.lower()

        # Reemplaza espacios y caracteres especiales con guiones
        slug = re.sub(r'[^a-z0-9ñáéíóú\-]', '-', slug)

        # Elimina guiones múltiples
        slug = re.sub(r'-+', '-', slug)

        # Elimina guiones al inicio/final
        slug = slug.strip('-')

        # Limita a 100 caracteres
        return slug[:100]

    @staticmethod
    def generate_seo_title(title: str, author: str = None, max_length: int = 60) -> str:
        """
        Genera título SEO para WP All Import
        Formato: "Título | Autor"
        """
        if not title:
            return ""

        title = WPAllImportConverter.clean_dilve_text(title)

        if author:
            author = WPAllImportConverter.clean_dilve_text(author)
            seo_title = f"{title} | {author}"
        else:
            seo_title = title

        if len(seo_title) > max_length:
            seo_title = seo_title[:max_length].rsplit(' ', 1)[0]

        return seo_title.strip()

    @staticmethod
    def dilve_to_wp_all_import(dilve_row: Dict) -> Dict:
        """
        Convierte fila DILVE → WP All Import Step 4 exacto
        
        Mapeo de campos:
        - titulo → post_title (SEO optimizado)
        - resumen/descripcion → post_content
        - isbn13 → _id (identificador único)
        - precio → _regular_price
        - stock → _stock + post_status
        """
        try:
            # Extrae campos DILVE
            isbn13 = dilve_row.get('isbn13', '').strip()
            titulo = dilve_row.get('titulo', dilve_row.get('title', '')).strip()
            autor = dilve_row.get('autor', dilve_row.get('author', '')).strip()
            resumen = dilve_row.get('resumen', dilve_row.get('description', '')).strip()
            precio = dilve_row.get('precio', dilve_row.get('price', '0')).strip()
            precio_oferta = dilve_row.get('precio_oferta', dilve_row.get('sale_price', '')).strip()
            stock = dilve_row.get('stock', '0').strip()
            materia = dilve_row.get('materia_ibic', dilve_row.get('categories', 'General')).strip()
            portada_url = dilve_row.get('portada_url', dilve_row.get('images', '')).strip()

            # Limpieza crítica
            title_clean = WPAllImportConverter.clean_dilve_text(titulo)
            desc_clean = WPAllImportConverter.clean_dilve_text(resumen, max_length=5000)
            author_clean = WPAllImportConverter.clean_dilve_text(autor)

            # SEO fields
            seo_title = WPAllImportConverter.generate_seo_title(title_clean, author_clean)
            slug = WPAllImportConverter.generate_wp_slug(title_clean, author_clean)

            # Excerpt (primeras 155 caracteres)
            excerpt = desc_clean[:155] + '...' if len(desc_clean) > 155 else desc_clean

            # Stock logic
            try:
                stock_int = int(stock) if stock else 0
            except ValueError:
                stock_int = 0

            stock_status = 'instock' if stock_int > 0 else 'out_of_stock'
            post_status = 'publish' if stock_status == 'instock' else 'draft'

            # Precio
            try:
                regular_price = float(precio.replace(',', '.')) if precio else 0.0
            except ValueError:
                regular_price = 0.0

            try:
                sale_price = float(precio_oferta.replace(',', '.')) if precio_oferta else ''
            except ValueError:
                sale_price = ''

            # SKU basado en últimos 6 dígitos ISBN
            sku = f"LIB{isbn13[-6:]}" if isbn13 else "LIB000000"

            return {
                '_id': isbn13,
                'post_title': seo_title,
                'post_content': desc_clean,
                'post_excerpt': excerpt,
                '_sku': sku,
                '_regular_price': str(regular_price),
                '_sale_price': str(sale_price) if sale_price else '',
                '_stock': str(stock_int),
                '_manage_stock': '1',
                '_virtual': '0',
                '_downloadable': '0',
                'product_cat': materia,
                'tax_status': 'taxable',
                'post_status': post_status,
                'post_name': slug,
                'images': portada_url,
                'post_parent': '',
                'menu_order': '0',
                '_weight': '',
                '_length': '',
                '_width': '',
                '_height': '',
                '_shipping_class': '',
                'attribute_pa_color': '',
                'attribute_pa_size': '',
                'attribute_pa_material': ''
            }

        except Exception as e:
            logger.error(f"Error converting row: {e}")
            return None

    @staticmethod
    def process_dilve_csv(
        input_file: str,
        output_file: str,
        delimiter: str = ';'
    ) -> Dict:
        """
        Procesa CSV DILVE → WP All Import perfecto
        
        Args:
            input_file: Ruta del CSV DILVE
            output_file: Ruta del CSV WP All Import
            delimiter: Delimitador del CSV (default: ;)
        
        Returns:
            {
                'total': 100,
                'instock': 75,
                'out_of_stock': 25,
                'errors': 0,
                'output_file': 'path/to/file.csv'
            }
        """
        wp_rows = []
        error_count = 0

        try:
            # Lee CSV DILVE
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                if not reader.fieldnames:
                    raise ValueError("CSV vacío o sin headers")

                for row_num, row in enumerate(reader, 1):
                    try:
                        wp_row = WPAllImportConverter.dilve_to_wp_all_import(row)
                        if wp_row:
                            wp_rows.append(wp_row)
                        else:
                            error_count += 1
                    except Exception as e:
                        logger.error(f"Error en fila {row_num}: {e}")
                        error_count += 1

            # Escribe CSV WP All Import (drag&drop Step 4)
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=WP_ALL_IMPORT_FIELDS)
                writer.writeheader()
                writer.writerows(wp_rows)

            # Estadísticas
            instock_count = len([r for r in wp_rows if r['post_status'] == 'publish'])
            out_of_stock_count = len([r for r in wp_rows if r['post_status'] == 'draft'])

            result = {
                'status': 'success',
                'total': len(wp_rows),
                'instock': instock_count,
                'out_of_stock': out_of_stock_count,
                'errors': error_count,
                'output_file': output_file,
                'percentage_instock': round((instock_count / len(wp_rows) * 100) if wp_rows else 0, 1)
            }

            logger.info(f"WP All Import conversion: {result}")
            return result

        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'total': 0,
                'errors': error_count
            }

    @staticmethod
    def to_wp_all_import_csv(cleaned_rows: List[Dict]) -> str:
        """
        Convierte lista de filas limpias a CSV WP All Import
        
        Args:
            cleaned_rows: Lista de diccionarios con datos limpios
        
        Returns:
            String con contenido CSV
        """
        if not cleaned_rows:
            return ""

        output = []

        # Headers
        output.append(','.join(WP_ALL_IMPORT_FIELDS))

        # Rows
        for row in cleaned_rows:
            wp_row = WPAllImportConverter.dilve_to_wp_all_import(row)
            if wp_row:
                csv_row = [
                    str(wp_row.get(field, '')).replace(',', ';')
                    for field in WP_ALL_IMPORT_FIELDS
                ]
                output.append(','.join(f'"{val}"' for val in csv_row))

        return '\n'.join(output)


class WPAllImportStats:
    """Estadísticas y análisis para WP All Import"""

    @staticmethod
    def analyze_wp_import(wp_rows: List[Dict]) -> Dict:
        """
        Analiza datos para WP All Import
        """
        if not wp_rows:
            return {}

        total = len(wp_rows)
        instock = len([r for r in wp_rows if r['post_status'] == 'publish'])
        out_of_stock = total - instock

        # Categorías
        categories = {}
        for row in wp_rows:
            cat = row.get('product_cat', 'General')
            categories[cat] = categories.get(cat, 0) + 1

        # Rango de precios
        prices = []
        for row in wp_rows:
            try:
                price = float(row.get('_regular_price', 0))
                if price > 0:
                    prices.append(price)
            except ValueError:
                pass

        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        return {
            'total_products': total,
            'instock': instock,
            'out_of_stock': out_of_stock,
            'percentage_instock': round((instock / total * 100) if total > 0 else 0, 1),
            'categories': categories,
            'avg_price': round(avg_price, 2),
            'min_price': round(min_price, 2),
            'max_price': round(max_price, 2),
            'total_value': round(sum(prices), 2)
        }

    @staticmethod
    def generate_import_report(wp_rows: List[Dict]) -> str:
        """
        Genera reporte de importación para WP All Import
        """
        stats = WPAllImportStats.analyze_wp_import(wp_rows)

        report = f"""
╔════════════════════════════════════════════════════════════╗
║         WP All Import - Reporte de Importación             ║
╚════════════════════════════════════════════════════════════╝

📊 ESTADÍSTICAS GENERALES
├─ Total de productos: {stats.get('total_products', 0)}
├─ Con stock: {stats.get('instock', 0)} ({stats.get('percentage_instock', 0)}%)
└─ Sin stock: {stats.get('out_of_stock', 0)}

💰 PRECIOS
├─ Precio promedio: €{stats.get('avg_price', 0):.2f}
├─ Precio mínimo: €{stats.get('min_price', 0):.2f}
├─ Precio máximo: €{stats.get('max_price', 0):.2f}
└─ Valor total: €{stats.get('total_value', 0):.2f}

📚 CATEGORÍAS
"""
        for cat, count in stats.get('categories', {}).items():
            report += f"├─ {cat}: {count} productos\n"

        report += """
✅ LISTO PARA IMPORTAR EN WORDPRESS
├─ Formato: CSV (Step 4 WP All Import)
├─ Encoding: UTF-8
├─ Delimitador: Coma
└─ Campos: 22 (todos configurados)

🚀 PRÓXIMOS PASOS
1. Descarga el CSV
2. Abre WP All Import en WordPress
3. Selecciona "Create New Import"
4. Sube el CSV
5. Mapea campos (ya están listos)
6. Revisa preview
7. ¡Importa!
"""
        return report


# Ejemplo de uso
if __name__ == "__main__":
    # Procesar CSV DILVE
    result = WPAllImportConverter.process_dilve_csv(
        'data/mock_dilve_dirty.csv',
        'data/wp_all_import_ready.csv'
    )

    print(f"✅ {result['total']} productos procesados")
    print(f"   - Con stock: {result['instock']}")
    print(f"   - Sin stock: {result['out_of_stock']}")
    print(f"   - Errores: {result['errors']}")
    print(f"\n📁 Archivo: {result['output_file']}")
