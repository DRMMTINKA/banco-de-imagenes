import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

@st.cache_data
def cargar_datos():
    df = pd.read_excel("datos.xlsx")
    
    # 1. BUSCADOR DE TÍTULOS: Encuentra los títulos correctos
    titulos_encontrados = False
    for i, row in df.iterrows():
        # Convertimos todo a mayúsculas para que sea fácil de encontrar
        valores = [str(v).upper().strip() for v in row.values]
        if 'PROMOTORA' in valores:
            df.columns = valores
            df = df.iloc[i+1:].reset_index(drop=True)
            titulos_encontrados = True
            break
            
    if not titulos_encontrados:
        df.columns = [str(c).upper().strip() for c in df.columns]

    # 2. LIMPIEZA EXTREMA: Rellenamos las celdas vacías para evitar el error "NaN"
    df = df.dropna(how='all') 
    df = df.fillna("") 
    df = df.astype(str).replace('nan', '') 
    
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error("No se pudo leer el archivo 'datos.xlsx'.")
    st.stop()

st.sidebar.header("🔍 Buscador")

# 3. BÚSQUEDA FLEXIBLE: Buscamos columnas aunque estén escritas ligeramente distinto
col_promotora = next((c for c in df.columns if 'PROMOTORA' in c), None)
col_carpeta = next((c for c in df.columns if 'CARPET' in c), None)
col_ganador = next((c for c in df.columns if 'GANADOR' in c), None)

if col_promotora:
    # Quitamos espacios vacíos de la lista de filtros
    promotoras = sorted([p for p in df[col_promotora].unique() if p.strip() != ""])
    promotora_seleccionada = st.sidebar.multiselect("Buscar por Promotora:", promotoras)

    if promotora_seleccionada:
        df_filtrado = df[df[col_promotora].isin(promotora_seleccionada)]
    else:
        df_filtrado = df
else:
    st.error("Error: No detecto la columna PROMOTORA en tu Excel.")
    st.stop()

st.subheader("📊 Base de Datos de Ganadores")
st.dataframe(df_filtrado)

st.markdown("---")
st.subheader("📥 Descargar Archivos (Fotos y Actas)")

if col_carpeta and col_ganador:
    st.write("Expande el nombre del ganador para descargar sus archivos.")
    
    carpetas_mostradas = 0
    
    for index, row in df_filtrado.iterrows():
        carpeta = str(row[col_carpeta]).strip()
        ganador = str(row[col_ganador]).strip()
        
        # Verificamos si la carpeta existe en el sistema
        if carpeta != "" and os.path.exists(carpeta) and os.path.isdir(carpeta):
            carpetas_mostradas += 1
            with st.expander(f"👤 {ganador} (Código: {carpeta})"):
                archivos = os.listdir(carpeta)
                if len(archivos) > 0:
                    columnas = st.columns(len(archivos))
                    for i, archivo in enumerate(archivos):
                        ruta_archivo = os.path.join(carpeta, archivo)
                        if os.path.isfile(ruta_archivo) and archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                            with open(ruta_archivo, "rb") as f:
                                columnas[i].download_button(
                                    label=f"⬇️ Descargar {archivo}",
                                    data=f,
                                    file_name=archivo,
                                    mime="image/jpeg",
                                    # Generamos una clave única para cada botón
                                    key=f"btn_{carpeta}_{archivo}_{index}" 
                                )
                else:
                    st.info("La carpeta existe en el sistema pero no tiene archivos adentro.")
                    
    if carpetas_mostradas == 0:
        st.info("💡 Selecciona a una promotora arriba, o asegúrate de que los códigos de la columna coincidan con los nombres de las carpetas que subiste a GitHub.")

else:
    st.error("Faltan las columnas de Carpeta o Ganador en el Excel.")
