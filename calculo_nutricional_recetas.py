# ============================================================
# ⚗️ Cálculo nutricional a partir de recetas limpias y TPCA (join por código + grupo)
# ============================================================

import pandas as pd
from pathlib import Path

# ============================================================
# 📂 Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

FILE_RECETAS = DATA_PROCESSED / "recetas_calculo_clean.csv"
FILE_TPCA = DATA_PROCESSED / "tablas_peruanas_clean.csv"
OUTPUT_FILE = REPORTS_DIR / "recetas_calculo_nutricional.xlsx"
OUTPUT_FAIL = REPORTS_DIR / "recetas_sin_match.xlsx"

# ============================================================
# 🧮 Función principal
# ============================================================
def calcular_info_nutricional():
    """
    Calcula la información nutricional total de cada receta
    al unir la base de recetas limpias con la TPCA (Tablas Peruanas de Composición de Alimentos)
    según código + grupo de alimento.
    """
    print("📘 Cargando archivos...")
    df_recetas = pd.read_csv(FILE_RECETAS, sep=None, engine="python")
    df_tpca = pd.read_csv(FILE_TPCA, sep=None, engine="python", on_bad_lines="skip")

    # ============================================================
    # 🧼 Normalizar nombres de columnas
    # ============================================================
    df_recetas.columns = df_recetas.columns.str.lower().str.strip()
    df_tpca.columns = df_tpca.columns.str.lower().str.strip()

    # ============================================================
    # 🔍 Definir columnas clave
    # ============================================================
    col_codigo_receta = "codigo_del_alimento_tpca_2017"
    col_grupo_receta = "grupo_alimento_tpca2017"
    col_codigo_tpca = "codigo"
    col_grupo_tpca = "grupo"
    col_peso = "peso_neto__racion_g"

    # Validar existencia de columnas clave
    for col in [col_codigo_receta, col_grupo_receta, col_peso]:
        if col not in df_recetas.columns:
            raise ValueError(f"❌ No se encontró la columna '{col}' en recetas.")
    for col in [col_codigo_tpca, col_grupo_tpca]:
        if col not in df_tpca.columns:
            raise ValueError(f"❌ No se encontró la columna '{col}' en TPCA.")

    # ============================================================
    # 🧩 Seleccionar columnas nutricionales (habitualmente 3→26)
    # ============================================================
    nutri_cols = df_tpca.columns[3:27]
    print(f"📊 Columnas nutricionales detectadas: {len(nutri_cols)}")

    # ============================================================
    # 🔠 Estandarizar claves (convertir a texto limpio)
    # ============================================================
    def normalize_code(x):
        if pd.isna(x):
            return ""
        x = str(x).strip().upper()
        if x.replace(".", "", 1).isdigit():
            x = str(int(float(x)))  # Ej: 38.0 → "38"
        return x

    df_recetas[col_codigo_receta] = df_recetas[col_codigo_receta].apply(normalize_code)
    df_recetas[col_grupo_receta] = df_recetas[col_grupo_receta].astype(str).str.strip().str.upper()

    df_tpca[col_codigo_tpca] = df_tpca[col_codigo_tpca].apply(normalize_code)
    df_tpca[col_grupo_tpca] = df_tpca[col_grupo_tpca].astype(str).str.strip().str.upper()

    # ============================================================
    # 🔗 Unir tablas por código + grupo
    # ============================================================
    merged = pd.merge(
        df_recetas,
        df_tpca[[col_codigo_tpca, col_grupo_tpca] + nutri_cols.tolist()],
        left_on=[col_codigo_receta, col_grupo_receta],
        right_on=[col_codigo_tpca, col_grupo_tpca],
        how="left",
        validate="m:1"
    )

    # Diagnóstico de coincidencias
    sin_match_mask = merged[nutri_cols].isna().all(axis=1)
    n_sin = int(sin_match_mask.sum())
    n_total = len(merged)
    print(f"📍 Coincidencias encontradas: {n_total - n_sin} / {n_total}")

    # ============================================================
    # ⚖️ Calcular nutrientes ajustados por peso (por 100 g)
    # ============================================================
    peso = pd.to_numeric(merged[col_peso], errors="coerce").fillna(0)
    for col in nutri_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce") * (peso / 100)

    # ============================================================
    # 🧱 Seleccionar columnas finales
    # ============================================================
    columnas_receta = merged.columns[:20]  # primeras columnas informativas
    columnas_finales = list(columnas_receta) + list(nutri_cols)
    df_final = merged[columnas_finales]

    # ============================================================
    # 💾 Guardar resultados
    # ============================================================
    df_final.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Archivo con resultados guardado en: {OUTPUT_FILE}")

    if n_sin > 0:
        merged.loc[sin_match_mask, [col_codigo_receta, col_grupo_receta]].drop_duplicates().to_excel(
            OUTPUT_FAIL, index=False
        )
        print(f"⚠️ Ingredientes sin coincidencia guardados en: {OUTPUT_FAIL}")

    # ============================================================
    # 👀 Vista previa
    # ============================================================
    print("\n==============================")
    print("🔝 VISTA PREVIA DEL RESULTADO")
    print("==============================")
    print(df_final.head())
    print(f"\n📊 Filas: {len(df_final)} | Columnas: {len(df_final.columns)}")

    return df_final


# ============================================================
# 🚀 Ejecución directa (modo script)
# ============================================================
if __name__ == "__main__":
    calcular_info_nutricional()
