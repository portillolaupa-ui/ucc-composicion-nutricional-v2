# ============================================================
# 🧹 Limpieza única: Tablas Peruanas de Composición de Alimentos 2017
# ============================================================

import pandas as pd
from pathlib import Path

# ============================================================
# 📂 Configuración de rutas
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# ============================================================
# 🧩 Limpieza única de la tabla
# ============================================================
def limpiar_tabla_peruana():
    file = DATA_RAW / "TABLAS_PERUANAS_DE_COMPOSICIÓN_DE_alimentos 2017.xlsx"

    if not file.exists():
        raise FileNotFoundError(f"No se encontró el archivo en {file}")

    print("📘 Cargando archivo:", file.name)
    xls = pd.ExcelFile(file)
    hoja = xls.sheet_names[0]
    print(f"📄 Hoja detectada: {hoja}")

    # Cargar datos
    df = pd.read_excel(xls, hoja)
    print(f"📊 Filas originales: {len(df)} | Columnas: {len(df.columns)}")

    # ============================================================
    # 🧼 Limpieza
    # ============================================================
    # Estandarizar nombres de columnas
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[^a-z0-9_]", "", regex=True)
    )

    # Eliminar filas vacías o duplicadas
    df = df.dropna(how="all").drop_duplicates()

    # Estandarizar texto en columnas tipo string
    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].astype(str).str.strip().str.upper()

    # ============================================================
    # 💾 Guardar
    # ============================================================
    output_path = DATA_PROCESSED / "tablas_peruanas_clean.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Limpieza completada. Archivo guardado en: {output_path}")
    print(f"📊 Filas finales: {len(df)} | Columnas: {len(df.columns)}")

# ============================================================
# 🚀 Ejecución
# ============================================================
if __name__ == "__main__":
    limpiar_tabla_peruana()