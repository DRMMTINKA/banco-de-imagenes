import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("datos.xlsx")
    
    # BUSCADOR INTELIGENTE: Si hay filas vacías arriba, busca la fila real de los títulos
    if 'PROMOTORA' not in df.columns:
        for i, row in df.iterrows():
            # Si encuentra la palabra PROMOTORA en esta fila, la convierte en los encabezados
            if 'PROMOTORA' in list(row.astype(str)):
                df.columns = row
                # Recorta la tabla para que empiece a partir de los datos reales
                df = df.iloc[i+1:].reset_index(drop=True)
                break
                
    # Limpia cualquier espacio en blanco invisible
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error("Por favor asegúrate de que el archivo se llame 'datos.xlsx'.")
    st.stop()

st.sidebar.header("🔍 Buscador")

if 'PROMOTORA' in df.columns:
    promotoras = df['PROMOTORA'].dropna().unique().tolist()
    promotora_seleccionada = st.sidebar.multiselect("Buscar por Promotora:", promotoras)

    if promotora_seleccionada:
        df_filtrado = df[df['PROMOTORA'].isin(promotora_seleccionada)]
    else:
        df_filtrado = df
else:
    st.error("No se encontró la columna 'PROMOTORA'. Revisa tu archivo Excel.")
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
