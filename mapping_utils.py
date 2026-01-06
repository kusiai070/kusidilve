import re
import unicodedata
from typing import List, Dict, Optional

def normalize_header(header: str) -> str:
    """
    Normaliza una cabecera: minúsculas, sin acentos, sin espacios extras ni caracteres raros.
    """
    if not header:
        return ""
    
    # A minúsculas y strip
    text = header.lower().strip()
    
    # Quitar acentos
    text = unicodedata.normalize('NFD', text)
    text = "".join([c for c in text if unicodedata.category(c) != 'Mn'])
    
    # Quitar caracteres que no sean letras, números o guiones/guiones bajos
    text = re.sub(r'[^a-z0-9_\- ]', '', text)
    
    # Reemplazar espacios por guiones bajos
    text = text.replace(' ', '_')
    
    # Colapsar guiones bajos múltiples
    text = re.sub(r'_+', '_', text)
    
    return text.strip('_')

def suggest_mapping(headers: List[str]) -> Dict[str, str]:
    """
    Sugiere un mapeo campo_kusidilve -> header_original_del_usuario.
    """
    # Sinónimos para heurística
    synonyms = {
        'isbn13': ['isbn', 'isbn13', 'ean', 'ean13', 'codigo_barras', 'barcode', 'ean_13'],
        'sku': ['sku', 'referencia', 'ref', 'cod', 'codigo', 'id_producto', 'identificador'],
        'post_title': ['titulo', 'title', 'nombre', 'denominacion', 'nombre_libro', 'obra'],
        'author': ['autor', 'autores', 'writer', 'creador', 'firma', 'author', 'escritor'],
        'publisher': ['editorial', 'publisher', 'editor', 'sello'],
        'regular_price': ['pvp', 'precio', 'precio_venta', 'price', 'coste', 'venta'],
        'stock': ['stock', 'existencias', 'unidades', 'cantidad', 'disponibles', 'count', 'qty'],
        'post_content': ['descripcion', 'resumen', 'contenido', 'sinopsis', 'texto', 'description'],
        'image_url': ['imagen', 'portada', 'url_imagen', 'image', 'picture', 'foto', 'img_url'],
        'category_main': ['categoria', 'materia', 'tema', 'genre', 'genero', 'seccion'],
    }

    mapping = {}
    normalized_headers = {normalize_header(h): h for h in headers}

    for kusi_field, synonym_list in synonyms.items():
        # Intento 1: Match exacto con el nombre del campo Kusi
        if kusi_field in normalized_headers:
            mapping[kusi_field] = normalized_headers[kusi_field]
            continue
            
        # Intento 2: Match con sinónimos
        found = False
        for syn in synonym_list:
            if syn in normalized_headers:
                mapping[kusi_field] = normalized_headers[syn]
                found = True
                break
        
        # Intento 3: Contiene substring (más agresivo)
        if not found:
            for syn in synonym_list:
                for norm_h, original_h in normalized_headers.items():
                    if syn in norm_h:
                        mapping[kusi_field] = original_h
                        found = True
                        break
                if found: break

    return mapping
