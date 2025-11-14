# ============================================================
# 🍽️ Dashboard de Cálculo Nutricional de Recetas – MIDIS / ROAR (mejorado UX/UI)
# ============================================================

import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from clean_recetas_calculo import limpiar_recetas as procesar_excel_recetas
from calculo_nutricional_recetas import calcular_info_nutricional


# ============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="Cálculo Nutricional de Recetas", page_icon="🍲", layout="wide")
st.title("Cálculo nutricional de recetas - UCC")

# ============================================================
# 🎨 ESTILOS VISUALES (solo estética)
# ============================================================
st.markdown("""
<style>
/* ====== GENERAL ====== */
body, .stApp {
    background-color: #f8f9fb;
    font-family: 'Inter', sans-serif;
    color: #333333;
}

/* ====== TITULOS ====== */
h1 {
    font-size: 2.2rem !important;
    color: #004C97;
    font-weight: 700;
    margin-bottom: 1rem;
}
h2, h3, h4 {
    color: #003366;
    font-weight: 600;
}
.stSubheader {
    font-size: 1.2rem !important;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

/* ====== SIDEBAR ====== */
section[data-testid="stSidebar"] {
    background-color: #f3f6fa !important;
    border-right: 1px solid #e0e4ea;
}
section[data-testid="stSidebar"] .stHeader {
    font-size: 1rem !important;
    font-weight: 600;
    color: #003366;
}

/* ====== BOTONES ====== */
.stButton button {
    background-color: #004C97;
    color: white;
    font-weight: 500;
    border-radius: 6px;
    padding: 0.4rem 1rem;
    border: none;
    transition: 0.2s ease-in-out;
}
.stButton button:hover {
    background-color: #0066cc;
    transform: scale(1.02);
}

/* ====== INPUTS ====== */
div[data-baseweb="select"] {
    border-radius: 6px !important;
}
input, select, textarea {
    border-radius: 6px !important;
}

/* ====== TABLAS ====== */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    background-color: white;
    padding: 0.8rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
thead tr th {
    background-color: #f1f4f8 !important;
    font-weight: 600 !important;
}
tbody tr:nth-child(even) {
    background-color: #fafbfc !important;
}
tbody tr:last-child td {
    font-weight: bold !important;
    background-color: #eef2f8 !important;
}

/* ====== DIVISORES (más compactos) ====== */
hr, .stMarkdown hr {
    border: 0.5px solid #d9e1ec !important;
    margin-top: 0.4rem !important;
    margin-bottom: 0.6rem !important;
    opacity: 0.8;
}

/* ====== DOWNLOAD BUTTON ====== */
.stDownloadButton button {
    background-color: #004C97;
    color: white;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.6rem 1.4rem;
    border: none;
    transition: 0.2s ease-in-out;
}
.stDownloadButton button:hover {
    background-color: #0066cc;
    transform: scale(1.03);
}

/* ====== CONTENEDORES ====== */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1.5rem;
}
.stColumn {
    padding-right: 0.5rem;
}
            
/* ====== AJUSTE DE TITULO SUPERIOR ====== */
h1 {
    margin-top: 2.8rem !important;   /* agrega espacio debajo del header */
    font-size: 2.4rem !important;
    color: #004C97;
    font-weight: 700;
}

            
</style>
""", unsafe_allow_html=True)

# ============================================================
# 📂 RUTAS BASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR.parent / "reports"

# ============================================================
# 🏷️ MAPEO DE NOMBRES (internos → legibles)
# ============================================================
PRETTY_MAP = {
    "nombre_de_receta": "Receta",
    "ingrediente_registrado": "Ingrediente",
    "ut": "UT",
    "tipo_receta": "Tipo de receta",
    "grupo_etareo_recet": "Grupo etáreo",
    "peso_neto__racion_g": "Peso neto por ración (g)",
    "energaenerc_kcal": "Energía (kcal)",
    "protenas_totalesprocnt_g": "Proteína (g)",
    "hierrofe_mg": "Hierro (mg)",
    "vitamina_a_equivalentes_totalesvita_μg": "Vitamina A (µg RAE)",
    "vitamina_cvitc_mg": "Vitamina C (mg)",
    "zinczn_mg": "Zinc (mg)",
    "grasa_totalfat_g": "Grasa total (g)",
    "carbohidratos_totaleschocdf_g": "Carbohidratos (g)",
    "fibra_dietariafibtg_g": "Fibra dietaria (g)",
    "calcioca_mg": "Calcio (mg)",
    "fsforop_mg": "Fósforo (mg)",
    "sodiona_mg": "Sodio (mg)",
    "potasiok_mg": "Potasio (mg)",
}
PRETTY_TO_INTERNAL = {v: k for k, v in PRETTY_MAP.items()}

def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: PRETTY_MAP.get(c, c) for c in df.columns})

def to_internal(cols_display: list[str]) -> list[str]:
    return [PRETTY_TO_INTERNAL.get(c, c) for c in cols_display]

# ============================================================
# 📤 CARGA Y PROCESAMIENTO
# ============================================================
uploaded_file = st.sidebar.file_uploader("Cargar archivo de recetas", type=["xlsx"])

if uploaded_file:
    # Guarda temporalmente el archivo subido
    temp_path = DATA_PROCESSED / "recetas_calculo.xlsx"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.sidebar.success("✅ Archivo cargado correctamente")

    # 🔹 Ejecuta la limpieza y genera el CSV limpio
    with st.spinner("🧼 Limpiando archivo de recetas..."):
        df_clean = procesar_excel_recetas(temp_path)
        st.session_state["df_clean"] = df_clean
        st.sidebar.success("✅ Archivo limpio generado correctamente")

if st.sidebar.button("🔄 Calcular información nutricional"):
    with st.spinner("Calculando información nutricional..."):
        df_final = calcular_info_nutricional()
        st.session_state["df_final"] = df_final
    st.success("✅ Cálculo completado correctamente.")

if "df_final" not in st.session_state:
    try:
        df_final = pd.read_excel(REPORTS_DIR / "recetas_calculo_nutricional.xlsx")
        st.session_state["df_final"] = df_final
    except FileNotFoundError:
        st.warning("⚠️ Aún no se ha generado el archivo de cálculos.")
        st.stop()

df_final = st.session_state["df_final"]

# ============================================================
# 🧩 CONFIGURACIÓN DE NUTRIENTES
# ============================================================
nutr_cols = [c for c in PRETTY_MAP if c.startswith(("energa", "prote", "hierro", "vitamina", "zinc", "grasa", "carbo", "fibra", "calcio", "fsforo", "sodio", "potasio"))]
nutr_disp = [PRETTY_MAP.get(c, c) for c in nutr_cols if c in df_final.columns]
nutr_default = [p for p in ["Energía (kcal)", "Proteína (g)", "Hierro (mg)", "Vitamina A (µg RAE)", "Vitamina C (mg)"] if p in nutr_disp]

# ============================================================
# 🔎 FILTROS
# ============================================================
st.markdown("---")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    ut_filt = st.multiselect("UT", sorted(df_final["ut"].dropna().unique()))
with col_f2:
    tipo_filt = st.multiselect("Tipo de receta", sorted(df_final["tipo_receta"].dropna().unique()))
with col_f3:
    grupo_filt = st.multiselect("Grupo etáreo", sorted(df_final["grupo_etareo_recet"].dropna().unique()))

df_filt = df_final.copy()
if ut_filt: df_filt = df_filt[df_filt["ut"].isin(ut_filt)]
if tipo_filt: df_filt = df_filt[df_filt["tipo_receta"].isin(tipo_filt)]
if grupo_filt: df_filt = df_filt[df_filt["grupo_etareo_recet"].isin(grupo_filt)]

# ============================================================
# 🍱 TABLA PRINCIPAL (resumen de recetas)
# ============================================================
st.markdown("---")
st.subheader("Recetas")

nutr_sel = st.multiselect("Selecciona nutrientes a mostrar", options=nutr_disp, default=nutr_default)
nutr_sel_internal = to_internal(nutr_sel)

raciones_resumen = st.number_input("Selecciona número de raciones", min_value=1, value=1, step=1, key="raciones_resumen")

if nutr_sel_internal:
    df_resumen = df_filt.groupby("nombre_de_receta", as_index=False)[nutr_sel_internal].sum()
    df_resumen[nutr_sel_internal] = df_resumen[nutr_sel_internal].apply(pd.to_numeric, errors="coerce").fillna(0) * raciones_resumen
    df_resumen = df_resumen.round(1)
    st.dataframe(rename_for_display(df_resumen), use_container_width=True)
else:
    st.info("Selecciona al menos un nutriente para ver el resumen.")

# ============================================================
# 🍽️ DETALLE DE RECETA
# ============================================================
st.markdown("---")
st.subheader("Detalle por receta")

col_r1, col_r2 = st.columns([3, 1])
receta_sel = col_r1.selectbox("Seleccionar receta", df_filt["nombre_de_receta"].unique())
raciones_detalle = col_r2.number_input("Selecciona número de raciones", min_value=1, value=1, step=1, key="raciones_detalle")

df_detalle = df_filt[df_filt["nombre_de_receta"] == receta_sel].copy()
cols_a_escalar = set(nutr_sel_internal + ["peso_neto__racion_g"])
df_detalle[list(cols_a_escalar)] = df_detalle[list(cols_a_escalar)].apply(pd.to_numeric, errors="coerce").fillna(0) * raciones_detalle
df_detalle[list(cols_a_escalar)] = df_detalle[list(cols_a_escalar)].round(1)

total_row = {col: ("TOTAL" if col == "ingrediente_registrado" else (df_detalle[col].sum() if col in nutr_sel_internal else None)) for col in ["ingrediente_registrado"] + list(cols_a_escalar)}
df_detalle_total = pd.concat([df_detalle, pd.DataFrame([total_row])], ignore_index=True)
st.dataframe(rename_for_display(df_detalle_total[["ingrediente_registrado", "peso_neto__racion_g"] + nutr_sel_internal]), use_container_width=True)

# ============================================================
# 📤 EXPORTAR RESULTADOS
# ============================================================
st.markdown("---")
st.subheader("Exportar resultados")

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    rename_for_display(df_resumen).to_excel(writer, index=False, sheet_name="Resumen")
    rename_for_display(df_final).to_excel(writer, index=False, sheet_name="Data completa")
    for sheet in writer.sheets.values():
        for i, col in enumerate(rename_for_display(df_resumen).columns):
            sheet.set_column(i, i, max(12, len(col) + 2))
buffer.seek(0)

st.download_button(
    label="💾 Descargar",
    data=buffer,
    file_name="recetas_nutricional_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
