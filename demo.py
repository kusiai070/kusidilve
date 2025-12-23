#!/usr/bin/env python3
"""
KusiDilve - Quick Start Demo
Demuestra la limpieza de CSV DILVE
"""

import csv
from csv_cleaner import CSVCleaner

def main():
    print("=" * 60)
    print("🚀 KusiDilve - CSV Cleaner Demo")
    print("=" * 60)
    print()

    # Lee CSV sucio
    print("📖 Leyendo CSV sucio...")
    with open('data/mock_dilve_dirty.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        dirty_rows = list(reader)

    print(f"✓ {len(dirty_rows)} libros cargados")
    print()

    # Muestra ejemplo sucio
    print("🔴 ANTES (Sucio):")
    print("-" * 60)
    first_dirty = dirty_rows[0]
    print(f"  Título: {first_dirty['titulo']}")
    print(f"  Descripción: {first_dirty['descripcion'][:50]}...")
    print(f"  Stock: {first_dirty['stock']}")
    print()

    # Limpia
    print("🧹 Limpiando...")
    cleaned_rows, error_count = CSVCleaner.clean_csv(dirty_rows)
    print(f"✓ {len(cleaned_rows)} libros limpios, {error_count} errores")
    print()

    # Muestra ejemplo limpio
    print("✅ DESPUÉS (Limpio):")
    print("-" * 60)
    first_clean = cleaned_rows[0]
    print(f"  Título: {first_clean['title']}")
    print(f"  SEO Title: {first_clean['seo_title']}")
    print(f"  Descripción: {first_clean['description_clean'][:50]}...")
    print(f"  Slug: {first_clean['slug']}")
    print(f"  Stock Status: {first_clean['stock_status']}")
    print(f"  SEO Score: {first_clean['score_seo']}/100")
    print()

    # Estadísticas
    print("📊 Estadísticas:")
    print("-" * 60)
    total_score = sum(r['score_seo'] for r in cleaned_rows)
    avg_score = total_score / len(cleaned_rows) if cleaned_rows else 0
    in_stock = sum(1 for r in cleaned_rows if r['stock_status'] == 'instock')
    out_of_stock = len(cleaned_rows) - in_stock

    print(f"  Total de libros: {len(cleaned_rows)}")
    print(f"  Con stock: {in_stock}")
    print(f"  Sin stock: {out_of_stock}")
    print(f"  Score SEO promedio: {avg_score:.1f}/100")
    print()

    # Exporta WooCommerce
    print("📥 Exportando a WooCommerce...")
    wc_csv = CSVCleaner.to_woocommerce_csv(cleaned_rows)
    with open('data/woocommerce_export.csv', 'w', encoding='utf-8') as f:
        f.write(wc_csv)
    print(f"✓ Exportado a: data/woocommerce_export.csv")
    print()

    # Tabla de comparación
    print("📋 Comparación de campos:")
    print("-" * 60)
    print(f"{'Campo':<20} {'Sucio':<30} {'Limpio':<30}")
    print("-" * 60)
    print(f"{'Título':<20} {first_dirty['titulo'][:28]:<30} {first_clean['title'][:28]:<30}")
    print(f"{'Descripción':<20} {first_dirty['descripcion'][:28]:<30} {first_clean['description_clean'][:28]:<30}")
    print(f"{'Stock Status':<20} {'N/A':<30} {first_clean['stock_status']:<30}")
    print(f"{'Slug':<20} {'N/A':<30} {first_clean['slug']:<30}")
    print()

    print("=" * 60)
    print("✨ Demo completado!")
    print("=" * 60)
    print()
    print("Próximos pasos:")
    print("1. pip install -r requirements.txt")
    print("2. uvicorn app:app --reload")
    print("3. Abre http://localhost:8000/templates/dashboard.html")
    print()

if __name__ == "__main__":
    main()
