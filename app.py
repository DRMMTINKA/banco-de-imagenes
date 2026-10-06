import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("datos.xlsx")
    # LÍNEA LIMPIADORA: Borra espacios en blanco ocultos en los títulos
    df.columns = df.columns.str.strip()
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error("Por favor asegúrate de que el archivo se llame 'datos.xlsx'.")
    st.stop()

st.sidebar.header("🔍 Buscador")

# Verificamos que la columna exista para evitar errores
if 'PROMOTORA' in df.columns:
    promotoras = df['PROMOTORA'].dropna().unique().tolist()
    promotora_seleccionada = st.sidebar.multiselect("Buscar por Promotora:", promotoras)

    if promotora_seleccionada:
        df_filtrado = df[df['PROMOTORA'].isin(promotora_seleccionada)]
    else:
        df_filtrado = df
else:
    st.error("No se encontró la columna 'PROMOTORA'. Las columnas detectadas son: " + ", ".join(df.columns))
    st.stop()

st.subheader("📊 Base de Datos de Ganadores")
st.dataframe(df_filtrado)

st.markdown("---")
st.subheader("📥 Descargar Archivos (Fotos y Actas)")
st.write("Expande el nombre del ganador para descargar sus archivos.")

if 'NOMBRE CARPET' in df.columns and 'NOMBRE GANADOR' in df.columns:
    for index, row in df_filtrado.iterrows():
        carpeta = str(row['NOMBRE CARPET']).strip()
        ganador = str(row['NOMBRE GANADOR'])
        
        # Si la subcarpeta existe, mostramos el desplegable con los botones
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
else:
    st.error("Faltan las columnas 'NOMBRE CARPET' o 'NOMBRE GANADOR' en el Excel.")
