import unittest
from thema_utils import map_thema_to_kusi

class TestThemaUtils(unittest.TestCase):
    def test_map_thema_exact_match(self):
        """Test exact matches for Thema codes"""
        self.assertEqual(map_thema_to_kusi("F"), "Ficción")
        self.assertEqual(map_thema_to_kusi("FB"), "Ficción Clásica")
        self.assertEqual(map_thema_to_kusi("Y"), "Educación y Textos de Enseñanza")

    def test_map_thema_prefix_match(self):
        """Test matches based on prefixes"""
        # "FBA" (Ficción Clásica Antigua - inventado) should map to "FB" (Ficción Clásica)
        self.assertEqual(map_thema_to_kusi("FBA"), "Ficción Clásica")
        # "JAB" should map to "JA"
        self.assertEqual(map_thema_to_kusi("JAB"), "Infantil y Juvenil: Ficción de Interés General")

    def test_map_thema_fallback(self):
        """Test fallback for unknown codes"""
        self.assertEqual(map_thema_to_kusi("X"), "Otros")
        self.assertEqual(map_thema_to_kusi("ZZZ"), "Otros")
        self.assertEqual(map_thema_to_kusi(""), "Sin Categoría")
        self.assertEqual(map_thema_to_kusi(None), "Sin Categoría")

    def test_case_insensitivity(self):
        """Test case insensitivity"""
        self.assertEqual(map_thema_to_kusi("fb"), "Ficción Clásica")
        self.assertEqual(map_thema_to_kusi("f"), "Ficción")

if __name__ == '__main__':
    unittest.main()
