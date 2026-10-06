import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

# Ya no usamos caché estricto para que la tabla se actualice al usar el formulario
def cargar_datos():
    if not os.path.exists("datos.xlsx"):
        return pd.DataFrame()
        
    df = pd.read_excel("datos.xlsx")
    
    titulos_encontrados = False
    for i, row in df.iterrows():
        valores = [str(v).upper().strip() for v in row.values]
        if 'PROMOTORA' in valores or 'PRODUCTO' in valores:
            df.columns = valores
            df = df.iloc[i+1:].reset_index(drop=True)
            titulos_encontrados = True
            break
            
    if not titulos_encontrados:
        df.columns = [str(c).upper().strip() for c in df.columns]

    df = df.dropna(how='all').fillna("")
    return df

df = cargar_datos()

# Detectar columnas clave automáticamente
col_producto = next((c for c in df.columns if 'PRODUCTO' in c), None)
col_terminal = next((c for c in df.columns if 'NOMBRE DE TERMINAL' in c), next((c for c in df.columns if 'TERMINAL' in c), None))
col_fecha = next((c for c in df.columns if 'FECHA DE CARGA' in c or 'FECHA' in c), None)
col_carpeta = next((c for c in df.columns if 'CARPET' in c), None)
col_ganador = next((c for c in df.columns if 'GANADOR' in c), None)

# Formatear la columna de fecha para que el filtro del ranking funcione bien
if col_fecha:
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce', dayfirst=True)

# Crear las 3 pestañas principales
tab1, tab2, tab3 = st.tabs(["📊 Base de Datos", "🏆 Ranking de Terminales", "📝 Ingresar Nuevo Ganador"])

# ---------------------------------------------------------
# PESTAÑA 1: BASE DE DATOS Y DESCARGAS
# ---------------------------------------------------------
with tab1:
    st.sidebar.header("🔍 Buscador Principal")
    
    # Filtro cambiado a PRODUCTO
    if col_producto:
        productos = sorted([p for p in df[col_producto].unique() if str(p).strip() != ""])
        prod_seleccionado = st.sidebar.multiselect("Buscar por PRODUCTO:", productos)

        if prod_seleccionado:
            df_filtrado = df[df[col_producto].isin(prod_seleccionado)]
        else:
            df_filtrado = df
    else:
        st.sidebar.warning("No se encontró la columna PRODUCTO")
        df_filtrado = df

    # Mostrar tabla convirtiendo fechas a texto para que no haya errores visuales
    st.dataframe(df_filtrado.astype(str), use_container_width=True)

    st.markdown("---")
    st.subheader("📥 Descargar Archivos")
    
    if col_carpeta and col_ganador:
        for index, row in df_filtrado.iterrows():
            carpeta = str(row[col_carpeta]).strip()
            ganador = str(row[col_ganador]).strip()
            
            if carpeta != "" and os.path.exists(carpeta) and os.path.isdir(carpeta):
                with st.expander(f"👤 {ganador} (Código: {carpeta})"):
                    archivos = os.listdir(carpeta)
                    # Filtramos para no mostrar el Thumbs.db
                    archivos_validos = [a for a in archivos if a.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    
                    if len(archivos_validos) > 0:
                        columnas = st.columns(len(archivos_validos))
                        for i, archivo in enumerate(archivos_validos):
                            ruta_archivo = os.path.join(carpeta, archivo)
                            with open(ruta_archivo, "rb") as f:
                                columnas[i].download_button(
                                    label=f"⬇️ Descargar {archivo}", 
                                    data=f, 
                                    file_name=archivo, 
                                    mime="image/jpeg", 
                                    key=f"btn_{carpeta}_{archivo}_{index}"
                                )
                    else:
                        st.info("Carpeta sin fotos válidas.")

# ---------------------------------------------------------
# PESTAÑA 2: RANKING DE TERMINALES
# ---------------------------------------------------------
with tab2:
    st.subheader("Top Terminales con más Ganadores")
    
    if col_terminal and col_fecha:
        fechas_validas = df[col_fecha].dropna()
        if not fechas_validas.empty:
            min_date = fechas_validas.min().date()
            max_date = fechas_validas.max().date()
            
            # Selector de rango de fechas
            rango_fechas = st.date_input("Filtrar Ranking por rango de fechas:", [min_date, max_date])
            
            # Aplicar filtro solo si seleccionaron inicio y fin
            if len(rango_fechas) == 2:
                fecha_inicio, fecha_fin = rango_fechas
                mask = (df[col_fecha].dt.date >= fecha_inicio) & (df[col_fecha].dt.date <= fecha_fin)
                df_ranking = df.loc[mask]
            else:
                df_ranking = df
        else:
            df_ranking = df
        
        # Agrupar y contar
        ranking = df_ranking[col_terminal].value_counts().reset_index()
        ranking.columns = ['Terminal', 'Cantidad de Ganadores']
        
        if not ranking.empty:
            col_grafico, col_tabla = st.columns([2, 1])
            with col_grafico:
                st.bar_chart(data=ranking.head(10), x='Terminal', y='Cantidad de Ganadores') # Muestra el Top 10
            with col_tabla:
                st.dataframe(ranking, use_container_width=True)
        else:
            st.info("No hay ganadores en este rango de fechas.")
    else:
        st.warning("Falta la columna TERMINAL o FECHA en el Excel para armar el ranking.")

# ---------------------------------------------------------
# PESTAÑA 3: FORMULARIO DE INGRESO
# ---------------------------------------------------------
with tab3:
    st.subheader("Registrar Nuevo Ganador y Subir Fotos")
    st.info("💡 Nota: El registro aparecerá en la tabla inmediatamente. (Guardado temporal de prueba).")
    
    with st.form("form_nuevo"):
        col1, col2 = st.columns(2)
        with col1:
            nuevo_terminal = st.text_input("Nombre de Terminal")
            nuevo_producto = st.text_input("Producto")
            nueva_fecha = st.date_input("Fecha de Carga")
        with col2:
            nuevo_ganador = st.text_input("Nombre del Ganador")
            nueva_carpeta = st.text_input("Código de Carpeta (Ej: 20260410-01)")
            
        fotos = st.file_uploader("Sube la foto del ganador y el acta", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        enviado = st.form_submit_button("Guardar Registro", type="primary")
        
        if enviado:
            if nueva_carpeta.strip() == "":
                st.error("Debes ingresar un Código de Carpeta.")
            else:
                # 1. Crear carpeta y guardar fotos
                os.makedirs(nueva_carpeta, exist_ok=True)
                for foto in fotos:
                    ruta_foto = os.path.join(nueva_carpeta, foto.name)
                    with open(ruta_foto, "wb") as f:
                        f.write(foto.getbuffer())
                
                # 2. Agregar al Excel
                nueva_fila = {c: "" for c in df.columns} 
                if col_terminal: nueva_fila[col_terminal] = nuevo_terminal
                if col_producto: nueva_fila[col_producto] = nuevo_producto
                if col_fecha: nueva_fila[col_fecha] = nueva_fecha
                if col_ganador: nueva_fila[col_ganador] = nuevo_ganador
                if col_carpeta: nueva_fila[col_carpeta] = nueva_carpeta
                
                df_nueva = pd.DataFrame([nueva_fila])
                df_final = pd.concat([df, df_nueva], ignore_index=True)
                
                # Guardar Excel 
                df_final.to_excel("datos.xlsx", index=False)
                
                st.success(f"✅ ¡Registro de {nuevo_ganador} guardado! Ve a la pestaña 'Base de Datos' para verlo.")
