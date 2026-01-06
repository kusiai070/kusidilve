"""
Thema Utils - Mapeo de códigos Thema a categorías Kusi
"""
from typing import Dict

# Mapeo simplificado de códigos Thema a categorías legibles
# Referencia: https://www.editeur.org/151/Thema/
THEMA_MAPPING: Dict[str, str] = {
    "F": "Ficción",
    "FA": "Ficción Moderna y Contemporánea",
    "FB": "Ficción Clásica",
    "FC": "Ficción: Géneros y Estilos",
    "FD": "Ficción: Ciencia Ficción y Fantasía",
    "FF": "Ficción: Crimen y Misterio",
    "FH": "Ficción: Suspense y Thriller",
    "FJ": "Ficción: Bélica",
    "FK": "Ficción: Terror y Sobrenatural",
    "FL": "Ficción: Erótica",
    "FM": "Ficción: Relatos Cortos",
    "FN": "Ficción: Histórica",
    "FP": "Ficción: Humorística",
    "FR": "Ficción: Romántica",
    "FS": "Ficción: De Aventuras",
    "FT": "Ficción: Deportes y Juegos",
    "FU": "Ficción: Distópica",
    "FV": "Ficción: Familiar",
    "FW": "Ficción: Religiosa y Espiritual",
    "FX": "Ficción: Narrativa Gráfica",
    "J": "Infantil, Juvenil y Didáctico",
    "JA": "Infantil y Juvenil: Ficción de Interés General",
    "JB": "Infantil y Juvenil: Ficción de Género",
    "Y": "Educación y Textos de Enseñanza",
    "P": "Matemáticas y Ciencia",
    "Q": "Filosofía y Religión",
    "R": "Tierra, Geografía, Medio Ambiente",
    "S": "Deportes y Actividades de Ocio",
    "T": "Tecnología, Ingeniería, Agricultura",
    "U": "Computación e Informática",
    "V": "Salud y Cuestiones Personales",
    "W": "Estilo de Vida, Deporte y Ocio",
}

def map_thema_to_kusi(thema_code: str) -> str:
    """
    Mapea un código Thema (o prefijo) a una categoría Kusi.
    """
    if not thema_code:
        return "Sin Categoría"
    
    code = str(thema_code).strip().upper()
    
    # Intento 1: Match exacto
    if code in THEMA_MAPPING:
        return THEMA_MAPPING[code]
    
    # Intento 2: Match por prefijo (ej: FB -> F, JAB -> JA)
    for length in range(len(code) - 1, 0, -1):
        prefix = code[:length]
        if prefix in THEMA_MAPPING:
            return THEMA_MAPPING[prefix]
            
    return "Otros"
