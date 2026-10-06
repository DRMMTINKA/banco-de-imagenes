import streamlit as st
import pandas as pd
import os

# Configuración inicial de la página
st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

# Leer el Excel
@st.cache_data
def cargar_datos():
    return pd.read_excel("datos.xlsx")

try:
    df = cargar_datos()
except Exception as e:
    st.error("Por favor asegúrate de que el archivo se llame 'datos.xlsx'.")
    st.stop()

# Crear un panel lateral para buscar
st.sidebar.header("🔍 Buscador")
promotoras = df['PROMOTORA'].dropna().unique().tolist()
promotora_seleccionada = st.sidebar.multiselect("Buscar por Promotora:", promotoras)

# Filtrar la tabla según lo que busque el usuario
if promotora_seleccionada:
    df_filtrado = df[df['PROMOTORA'].isin(promotora_seleccionada)]
else:
    df_filtrado = df

# Mostrar la tabla de Excel
st.subheader("📊 Base de Datos de Ganadores")
st.dataframe(df_filtrado)

st.markdown("---")
st.subheader("📥 Descargar Archivos (Fotos y Actas)")
st.write("Expande el nombre del ganador para descargar sus archivos.")

# Generar botones de descarga dinámicos
for index, row in df_filtrado.iterrows():
    carpeta = str(row['NOMBRE CARPET']).strip()
    ganador = str(row['NOMBRE GANADOR'])
    
    # Si la carpeta de este ganador existe en GitHub, mostramos sus fotos
    if os.path.exists(carpeta) and os.path.isdir(carpeta):
        with st.expander(f"👤 {ganador} (Código: {carpeta})"):
            archivos = os.listdir(carpeta)
            columnas = st.columns(len(archivos) if len(archivos) > 0 else 1)
            
            for i, archivo in enumerate(archivos):
                ruta_archivo = os.path.join(carpeta, archivo)
                if os.path.isfile(ruta_archivo):
                    with open(ruta_archivo, "rb") as f:
                        columnas[i].download_button(
                            label=f"⬇️ Descargar {archivo}",
                            data=f,
                            file_name=archivo,
                            mime="image/jpeg"
                        )
