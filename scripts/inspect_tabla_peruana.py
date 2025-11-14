# ============================================================
# 📋 Exportar resultado de df.info() a CSV
# ============================================================

import pandas as pd
from pathlib import Path
from io import StringIO

# ============================================================
# 📂 Configuración de rutas
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

file = DATA_PROCESSED / "tablas_peruanas_clean.csv"
output_file = OUTPUT_DIR / "info_tablas_peruanas.csv"

# ============================================================
# 📖 Leer CSV
# ============================================================
print(f"📘 Leyendo archivo: {file}")
df = pd.read_csv(file, sep=None, engine="python")

# ============================================================
# 🧩 Capturar el texto que muestra .info()
# ============================================================
buffer = StringIO()
df.info(buf=buffer)
info_str = buffer.getvalue()

# ============================================================
# 💾 Guardar el texto en CSV (una sola columna)
# ============================================================
info_lines = info_str.strip().split("\n")
info_df = pd.DataFrame({"info": info_lines})

info_df.to_csv(output_file, index=False, encoding="utf-8")
print(f"✅ Archivo CSV generado con info() en: {output_file}")