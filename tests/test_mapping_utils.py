import unittest
from mapping_utils import normalize_header, suggest_mapping

class TestMappingUtils(unittest.TestCase):
    def test_normalize_header(self):
        """Test header normalization"""
        self.assertEqual(normalize_header("Título"), "titulo")
        self.assertEqual(normalize_header("  ISBN  "), "isbn")
        self.assertEqual(normalize_header("Precio de Venta"), "precio_de_venta")
        self.assertEqual(normalize_header("Materia (IBIC)"), "materia_ibic")
        self.assertEqual(normalize_header("Código EAN-13"), "codigo_ean-13")
        self.assertEqual(normalize_header(""), "")

    def test_suggest_mapping_exact(self):
        """Test suggestions for exact matches"""
        headers = ["isbn13", "title", "author"]
        mapping = suggest_mapping(headers)
        self.assertEqual(mapping.get("isbn13"), "isbn13")
        self.assertEqual(mapping.get("post_title"), "title")
        self.assertEqual(mapping.get("author"), "author")

    def test_suggest_mapping_synonyms(self):
        """Test suggestions for synonyms"""
        headers = ["Codigo Barras", "Nombre del Libro", "Escritor", "PVP"]
        mapping = suggest_mapping(headers)
        self.assertEqual(mapping.get("isbn13"), "Codigo Barras")
        self.assertEqual(mapping.get("post_title"), "Nombre del Libro")
        self.assertEqual(mapping.get("author"), "Escritor")
        self.assertEqual(mapping.get("regular_price"), "PVP")

    def test_suggest_mapping_partial(self):
        """Test suggestions for partial matches"""
        headers = ["My SKU Code", "Book Description Text"]
        mapping = suggest_mapping(headers)
        # Assuming partial matching logic in mapping_utils works this way
        self.assertEqual(mapping.get("sku"), "My SKU Code")
        self.assertEqual(mapping.get("post_content"), "Book Description Text")

if __name__ == '__main__':
    unittest.main()
