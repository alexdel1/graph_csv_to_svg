try:
    from .csv_to_svg_c import csv_to_svg
    print("Import successful")
except ImportError as e:
    print(f"Import error: {e}")
