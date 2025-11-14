# ============================================================
# ⚗️ Cálculo nutricional a partir de recetas + TPCA (join por código + grupo)
# Genera Excel completo en /reports y retorna el DataFrame procesado
# ============================================================

from __future__ import annotations
import pandas as pd
from pathlib import Path
from datetime import datetime

# Rutas relativas al repo (ajusta si tu layout difiere)
REPO_ROOT = Path(__file__).resolve().parents[2]  # .../ucc-composicion-nutricional
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TPCA_PATH = DATA_PROCESSED / "tablas_peruanas_clean.csv"
OUTPUT_XLSX = REPORTS_DIR / "recetas_calculo_nutricional.xlsx"

# ------------ utilidades ------------
def _normalize_code(x) -> str:
    if pd.isna(x):
        return ""
    x = str(x).strip().upper()
    # Convierte "38.0" -> "38"
    try:
        if str(float(x)) == x or x.replace(".", "", 1).isdigit():
            x = str(int(float(x)))
    except Exception:
        pass
    return x

def _find_col(df: pd.DataFrame, needles: list[str]) -> str | None:
    cols = [c.lower().strip() for c in df.columns]
    for c in cols:
        for p in needles:
            if p in c:
                return c
    return None

def _safe_read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip")

def _safe_read_upload(upload) -> pd.DataFrame:
    """Lee Excel subido (BytesIO) tomando la primera hoja."""
    return pd.read_excel(upload)  # primera hoja por defecto

# ------------ núcleo ------------
def calcular_desde_upload(uploaded_excel) -> pd.DataFrame:
    """
    - Lee recetas desde el archivo subido (Excel)
    - Lee TPCA desde data/processed/tablas_peruanas_clean.csv
    - Cruza por (codigo + grupo) y escala nutrientes por peso_neto__racion_g
    - Guarda Excel completo en reports/recetas_calculo_nutricional.xlsx (con metadatos)
    - Retorna DataFrame procesado
    """
    if not TPCA_PATH.exists():
        raise FileNotFoundError(f"No se encontró TPCA en {TPCA_PATH}")

    # 1) Leer insumos
    df_rec = _safe_read_upload(uploaded_excel)
    if df_rec is None or df_rec.empty:
        raise ValueError("El Excel de recetas está vacío o no se pudo leer.")

    df_tp = _safe_read_csv(TPCA_PATH)
    if df_tp is None or df_tp.empty:
        raise ValueError("El archivo TPCA limpio está vacío. Revisa data/processed/tablas_peruanas_clean.csv.")

    # Normalizar nombres
    df_rec.columns = df_rec.columns.str.lower().str.strip()
    df_tp.columns = df_tp.columns.str.lower().str.strip()

    # 2) Detectar columnas clave en recetas
    col_cod_rec = _find_col(df_rec, ["codigo_del_alimento", "codigo_tpca", "codigo"])
    col_grp_rec = _find_col(df_rec, ["grupo_alimento", "grupo_tpca", "grupo"])
    col_peso    = _find_col(df_rec, ["peso_neto__racion_g", "peso_neto_racion", "racion_g", "peso_racion", "peso_g"])

    if not all([col_cod_rec, col_grp_rec, col_peso]):
        raise ValueError("No se detectaron columnas clave en recetas (codigo / grupo / peso). Revisa encabezados.")

    # 3) Detectar columnas clave en TPCA
    col_cod_tp = _find_col(df_tp, ["codigo"])
    col_grp_tp = _find_col(df_tp, ["grupo"])
    if not all([col_cod_tp, col_grp_tp]):
        raise ValueError("No se detectaron columnas clave en TPCA (codigo / grupo).")

    # 4) Columnas nutricionales TPCA (índices 3..26 inclusive)
    nutri_cols = df_tp.columns[3:27]
    if len(nutri_cols) == 0:
        raise ValueError("No se detectaron columnas nutricionales en TPCA (esperadas 3..26).")

    # 5) Normalizar claves y tipos
    df_rec[col_cod_rec] = df_rec[col_cod_rec].apply(_normalize_code)
    df_rec[col_grp_rec] = df_rec[col_grp_rec].astype(str).str.strip().str.upper()

    df_tp[col_cod_tp] = df_tp[col_cod_tp].apply(_normalize_code)
    df_tp[col_grp_tp] = df_tp[col_grp_tp].astype(str).str.strip().str.upper()

    # 6) Merge por dos claves
    merged = pd.merge(
        df_rec,
        df_tp[[col_cod_tp, col_grp_tp] + nutri_cols.tolist()],
        left_on=[col_cod_rec, col_grp_rec],
        right_on=[col_cod_tp, col_grp_tp],
        how="left",
        validate="m:1"
    )

    # 7) Escalar nutrientes por peso (por 100g)
    peso = pd.to_numeric(merged[col_peso], errors="coerce").fillna(0)
    for col in nutri_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce") * (peso / 100.0)

    # 8) Seleccionar columnas: recetas 0..18 + nutrientes 3..26
    cols_recetas = merged.columns[:19]
    out_cols = list(cols_recetas) + list(nutri_cols)
    df_final = merged[out_cols].copy()

    # 9) Guardar Excel completo (con metadatos)
    meta = pd.DataFrame({
        "campo": ["fecha_proceso", "fuente_tpca", "filas_resultado", "columnas_resultado"],
        "valor": [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  str(TPCA_PATH), len(df_final), len(df_final.columns)]
    })

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df_final.to_excel(writer, sheet_name="resultados", index=False)
        meta.to_excel(writer, sheet_name="metadatos", index=False)

    return df_final


# Exponer helpers para la app
def columnas_nutrientes(df_final: pd.DataFrame) -> list[str]:
    """Devuelve lista de columnas de nutrientes (asumimos que son las que vienen después de la 19)."""
    if df_final.shape[1] <= 19:
        return []
    return df_final.columns[19:].tolist()

def columnas_controles(df_final: pd.DataFrame) -> dict:
    """Intenta identificar columnas para filtros estándar."""
    def _col(df, needles):
        return _find_col(df, needles)

    return {
        "ut": _col(df_final, ["ut"]),
        "tipo_receta": _col(df_final, ["tipo_de_receta", "tipo_receta", "tipo"]),
        "grupo_etareo": _col(df_final, ["grupo_etareo", "grupo_etáreo", "grupo_edad"]),
        "nombre_receta": _col(df_final, ["nombre_de_receta", "receta", "nombre_receta"])
    }
