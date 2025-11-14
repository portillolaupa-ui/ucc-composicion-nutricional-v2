# # ============================================================
# # 🍽️ Limpieza profesional de archivo de recetas (para dashboard)
# # ============================================================

# import pandas as pd
# from pathlib import Path
# from io import StringIO

# # ============================================================
# # 📂 Configuración de rutas
# # ============================================================
# BASE_DIR = Path(__file__).resolve().parent
# DATA_RAW = BASE_DIR / "data" / "raw"
# DATA_PROCESSED = BASE_DIR / "data" / "processed"
# REPORTS_DIR = BASE_DIR / "reports"
# DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
# REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# # ============================================================
# # 🧩 Función de limpieza
# # ============================================================
# def limpiar_recetas(file_path=None):
#     """
#     Limpia y estandariza un archivo Excel de recetas.
#     - Estandariza nombres de columnas
#     - Elimina filas vacías o duplicadas
#     - Convierte texto a mayúsculas
#     - Convierte columnas numéricas
#     - Genera CSV limpio + Excel con info()
#     """

#     # Si no se pasa ruta, se usa el archivo por defecto
#     if file_path is None:
#         file_path = DATA_RAW / "recetas_calculo.xlsx"

#     print(f"Cargando archivo: {file_path.name}")
#     xls = pd.ExcelFile(file_path)
#     print(f"Hojas detectadas: {xls.sheet_names}")

#     # Cargar la primera hoja
#     df = pd.read_excel(xls, xls.sheet_names[0])
#     print(f"Filas originales: {len(df)} | Columnas: {len(df.columns)}")

#     # ============================================================
#     # 🧼 Limpieza general
#     # ============================================================
#     df.columns = (
#         df.columns.astype(str)
#         .str.strip()
#         .str.lower()
#         .str.replace(" ", "_")
#         .str.replace("[^a-z0-9_]", "", regex=True)
#     )

#     # Eliminar filas vacías o duplicadas
#     df = df.dropna(how="all").drop_duplicates()

#     # Limpiar texto en columnas tipo string
#     for col in df.select_dtypes(include=["object"]):
#         df[col] = df[col].astype(str).str.strip().str.upper()

#     # Convertir columnas numéricas si es posible
#     for col in df.columns:
#         df[col] = pd.to_numeric(df[col], errors="ignore")

#     # ============================================================
#     # 💾 Guardar versión limpia
#     # ============================================================
#     output_csv = DATA_PROCESSED / "recetas_calculo_clean.csv"
#     df.to_csv(output_csv, index=False, encoding="utf-8")
#     print(f"✅ Limpieza completada. CSV guardado en: {output_csv}")

#     # ============================================================
#     # 🧠 Guardar .info() como Excel
#     # ============================================================
#     buffer = StringIO()
#     df.info(buf=buffer)
#     info_text = buffer.getvalue()
#     info_df = pd.DataFrame({"info": info_text.strip().split("\n")})

#     output_excel = REPORTS_DIR / "info_recetas_calculo.xlsx"
#     info_df.to_excel(output_excel, index=False)
#     print(f"📄 Info guardada en: {output_excel}")

#     # ============================================================
#     # 👀 Mostrar primeras filas
#     # ============================================================
#     print("\n==============================")
#     print("🔝 VISTA PREVIA DEL CONTENIDO")
#     print("==============================")
#     print(df.head())

#     print(f"\n📊 Filas finales: {len(df)} | Columnas: {len(df.columns)}")

#     return df

# # ============================================================
# # 🚀 Ejecución directa
# # ============================================================
# if __name__ == "__main__":
#     limpiar_recetas()







# ============================================================
# 🍽️ Limpieza profesional de archivo de recetas (para dashboard)
# Versión 100% compatible con Streamlit Cloud (Python 3.13)
# SIN usar openpyxl
# ============================================================

import pandas as pd
from pathlib import Path
from io import StringIO
from xlsx2csv import Xlsx2csv
import tempfile
import os

# ============================================================
# 📂 Configuración de rutas
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 🧩 Función de limpieza (compatible sin openpyxl)
# ============================================================
def limpiar_recetas(file_path=None):
    """
    Limpia y estandariza un archivo Excel de recetas sin usar openpyxl.
    xlsx2csv convierte el XLSX a CSV → pandas lo procesa normal.
    """

    # Si no se pasa ruta, se usa el archivo por defecto
    if file_path is None:
        file_path = DATA_RAW / "recetas_calculo.xlsx"

    print(f"Cargando archivo XLSX sin openpyxl: {file_path}")

    # ============================================================
    # 🔄 Convertir XLSX → CSV temporal
    # ============================================================
    temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv").name
    Xlsx2csv(str(file_path), outputencoding="utf-8").convert(temp_csv)

    # Cargar CSV convertido
    df = pd.read_csv(temp_csv)

    # Eliminar archivo temporal
    os.remove(temp_csv)

    print(f"Filas cargadas: {len(df)} | Columnas: {len(df.columns)}")

    # ============================================================
    # 🧼 Limpieza general
    # ============================================================
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[^a-z0-9_]", "", regex=True)
    )

    # Eliminar filas vacías y duplicados
    df = df.dropna(how="all").drop_duplicates()

    # Limpiar columnas de tipo texto
    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Intentar convertir columnas numéricas
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    # ============================================================
    # 💾 Guardar versión limpia
    # ============================================================
    output_csv = DATA_PROCESSED / "recetas_calculo_clean.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"✅ CSV limpio guardado en: {output_csv}")

    # ============================================================
    # 🧠 Guardar info() en Excel
    # ============================================================
    buffer = StringIO()
    df.info(buf=buffer)
    info_text = buffer.getvalue()
    info_df = pd.DataFrame({"info": info_text.strip().split("\n")})

    output_excel = REPORTS_DIR / "info_recetas_calculo.xlsx"
    info_df.to_excel(output_excel, index=False)
    print(f"📄 Info guardada en: {output_excel}")

    # ============================================================
    # 🔍 Vista previa
    # ============================================================
    print("\n==============================")
    print("🔝 VISTA PREVIA DEL CONTENIDO")
    print("==============================")
    print(df.head())

    print(f"\n📊 Filas finales: {len(df)} | Columnas: {len(df.columns)}")

    return df


# ============================================================
# 🚀 Ejecución directa
# ============================================================
if __name__ == "__main__":
    limpiar_recetas()
