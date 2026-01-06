import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock slugify before importing CSVCleaner because it imports it at module level
sys.modules['slugify'] = MagicMock()
from csv_cleaner import CSVCleaner

class TestCSVCleaner(unittest.TestCase):
    def test_strip_html_tags(self):
        """Test HTML stripping"""
        self.assertEqual(CSVCleaner.strip_html_tags("<p>Hello</p>"), "Hello")
        self.assertEqual(CSVCleaner.strip_html_tags("<b>Bold</b> Text"), "Bold Text")
        self.assertEqual(CSVCleaner.strip_html_tags("No Tags"), "No Tags")

    def test_fix_utf8_encoding(self):
        """Test UTF-8 fixing"""
        # "Ã¡" is commonly "á" in broken UTF-8 interpreted as Latin-1
        self.assertEqual(CSVCleaner.fix_utf8_encoding("Camion"), "Camion") # No change
        # Not easily reproducible without exact broken string bytes, but testing basic passthrough
        self.assertEqual(CSVCleaner.fix_utf8_encoding(""), "")

    def test_clean_description(self):
        """Test description cleaning and truncating"""
        text = "<p>" + "A" * 600 + "</p>"
        cleaned = CSVCleaner.clean_description(text, max_length=500)
        self.assertLessEqual(len(cleaned), 503) # 500 + '...'
        self.assertFalse(cleaned.startswith("<p>"))

    def test_generate_seo_title(self):
        """Test SEO title generation"""
        title = "El Quijote"
        author = "Cervantes"
        self.assertEqual(CSVCleaner.generate_seo_title(title, author), "El Quijote | Cervantes")
        self.assertEqual(CSVCleaner.generate_seo_title(title), "El Quijote")

    @patch('csv_cleaner.slugify')
    def test_generate_slug(self, mock_slugify):
        """Test slug generation"""
        # Configure mock
        mock_slugify.side_effect = lambda x, max_length=100: x.lower().replace(" ", "-").replace("&", "")
        
        self.assertEqual(CSVCleaner.generate_slug("El Quijote", "Cervantes"), "el-quijote-cervantes")
        # Note: simplistic mock implementation for the test
        self.assertEqual(CSVCleaner.generate_slug("Cafe & Libros"), "cafe--libros")

    def test_clean_row_completa(self):
        """Test full row cleaning integration"""
        row = {
            "isbn13": "9781234567890",
            "titulo": "<b>Libro de Prueba</b>",
            "autor": "Autor Test",
            "descripcion": "<p>Descripción</p>",
            "precio": "10,50",
            "stock": "5",
            "thema_code": "FB"
        }
        cleaned = CSVCleaner.clean_row(row)
        
        self.assertEqual(cleaned['isbn13'], "9781234567890")
        self.assertEqual(cleaned['title'], "Libro de Prueba")
        self.assertEqual(cleaned['price'], 10.50)
        self.assertEqual(cleaned['stock'], 5)
        self.assertEqual(cleaned['stock_status'], "instock")
        self.assertEqual(cleaned['categories'], "Ficción Clásica") # Verified integration with thema_utils
        self.assertTrue(cleaned['score_seo'] > 0)

if __name__ == '__main__':
    unittest.main()
