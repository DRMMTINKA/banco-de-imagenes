import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Configuración inicial
st.set_page_config(page_title="Banco de Imágenes - La Tinka", layout="wide")
st.title("🏆 Banco de Imágenes y Actas - La Tinka")

def cargar_datos():
    if not os.path.exists("datos.xlsx"):
        return pd.DataFrame()
    
    df = pd.read_excel("datos.xlsx")
    titulos_encontrados = False
    for i, row in df.iterrows():
        valores = [str(v).upper().strip() for v in row.values]
        if 'PROMOTORA' in valores or 'PRODUCTO' in valores or 'TERMINAL' in valores:
            df.columns = valores
            df = df.iloc[i+1:].reset_index(drop=True)
            titulos_encontrados = True
            break
            
    if not titulos_encontrados:
        df.columns = [str(c).upper().strip() for c in df.columns]

    df = df.dropna(how='all').fillna("")
    return df

df = cargar_datos()

col_producto = next((c for c in df.columns if 'PRODUCTO' in c), None)
col_fecha = next((c for c in df.columns if 'FECHA' in c), None)
col_carpeta = next((c for c in df.columns if 'CARPET' in c), None)
col_ganador = next((c for c in df.columns if 'GANADOR' in c), None)

if col_fecha:
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce', dayfirst=True)

def cargar_terminales():
    if os.path.exists("terminales.csv"):
        return pd.read_csv("terminales.csv", dtype=str).fillna("")
    else:
        if 'TERMINAL' in df.columns and 'NOMBRE DE TERMINAL' in df.columns:
            term_df = df[['TERMINAL', 'NOMBRE DE TERMINAL', 'SUPERVISOR']].drop_duplicates(subset=['TERMINAL']).dropna(subset=['TERMINAL'])
            term_df = term_df[term_df['TERMINAL'] != ""]
            term_df.to_csv("terminales.csv", index=False)
            return term_df.astype(str)
        else:
            return pd.DataFrame(columns=['TERMINAL', 'NOMBRE DE TERMINAL', 'SUPERVISOR'])

df_terminales = cargar_terminales()

# ---------------------------------------------------------
# BARRA LATERAL IZQUIERDA
# ---------------------------------------------------------
st.sidebar.header("🔍 Buscador")
if col_producto:
    productos = sorted([p for p in df[col_producto].unique() if str(p).strip() != ""])
    prod_seleccionado = st.sidebar.multiselect("Filtrar por PRODUCTO:", productos)
    df_filtrado = df[df[col_producto].isin(prod_seleccionado)] if prod_seleccionado else df
else:
    df_filtrado = df

st.sidebar.markdown("---")
st.sidebar.header("📝 Nuevo Ganador")

lista_term = sorted(df_terminales['TERMINAL'].unique().tolist())
term_seleccionado = st.sidebar.selectbox("1. Código de Terminal:", [""] + lista_term)

nombre_auto = ""
super_auto = ""
if term_seleccionado != "":
    datos_term = df_terminales[df_terminales['TERMINAL'] == term_seleccionado].iloc[0]
    nombre_auto = datos_term.get('NOMBRE DE TERMINAL', '')
    super_auto = datos_term.get('SUPERVISOR', '')
    st.sidebar.success(f"**Sede:** {nombre_auto}\n**Sup:** {super_auto}")

with st.sidebar.form("form_nuevo"):
    nuevo_producto = st.text_input("Producto")
    nueva_fecha = st.date_input("Fecha de Carga")
    nuevo_ganador = st.text_input("Nombre del Ganador")
    nueva_carpeta = st.text_input("Código de Carpeta (Ej: 20261006-01)")
    
    # AÑADIDO: Permiso para subir archivos .webp
    fotos = st.file_uploader("Fotos (Ganador y Acta)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp'])
    
    enviado = st.form_submit_button("Guardar Registro", type="primary")
    
    if enviado:
        if term_seleccionado == "" or nueva_carpeta.strip() == "":
            st.error("Falta seleccionar Terminal o ingresar Código de Carpeta.")
        else:
            os.makedirs(nueva_carpeta, exist_ok=True)
            for foto in fotos:
                ruta_foto = os.path.join(nueva_carpeta, foto.name)
                with open(ruta_foto, "wb") as f:
                    f.write(foto.getbuffer())
            
            nueva_fila = {c: "" for c in df.columns} 
            if 'TERMINAL' in df.columns: nueva_fila['TERMINAL'] = term_seleccionado
            if 'NOMBRE DE TERMINAL' in df.columns: nueva_fila['NOMBRE DE TERMINAL'] = nombre_auto
            if 'SUPERVISOR' in df.columns: nueva_fila['SUPERVISOR'] = super_auto
            if col_producto: nueva_fila[col_producto] = nuevo_producto
            if col_fecha: nueva_fila[col_fecha] = pd.to_datetime(nueva_fecha)
            if col_ganador: nueva_fila[col_ganador] = nuevo_ganador
            if col_carpeta: nueva_fila[col_carpeta] = nueva_carpeta
            
            df_final = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            df_final.to_excel("datos.xlsx", index=False)
            st.success(f"✅ ¡{nuevo_ganador} guardado!")

# ---------------------------------------------------------
# ÁREA CENTRAL: PESTAÑAS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Base de Datos", "🏆 Ranking", "🏪 Maestro de Terminales"])

with tab1:
    if col_fecha:
        df_mostrar = df_filtrado.sort_values(by=col_fecha, ascending=False)
    else:
        df_mostrar = df_filtrado.iloc[::-1]
        
    st.dataframe(df_mostrar.astype(str), use_container_width=True)
    st.markdown("---")
    st.subheader("📥 Descargar Archivos")
    
    if col_carpeta and col_ganador:
        for index, row in df_mostrar.iterrows():
            carpeta = str(row[col_carpeta]).strip()
            ganador = str(row[col_ganador]).strip()
            
            etiqueta = ""
            if col_fecha and pd.notna(row[col_fecha]):
                if (datetime.now() - row[col_fecha]).days <= 3:
                    etiqueta = " 🆕 ¡NUEVA FOTO!"
            
            if carpeta != "" and os.path.exists(carpeta) and os.path.isdir(carpeta):
                with st.expander(f"👤 {ganador} (Código: {carpeta}){etiqueta}"):
                    
                    # AÑADIDO: Ahora también lee los archivos .webp de las carpetas
                    archivos = [a for a in os.listdir(carpeta) if a.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    
                    if len(archivos) > 0:
                        columnas = st.columns(len(archivos))
                        for i, archivo in enumerate(archivos):
                            with open(os.path.join(carpeta, archivo), "rb") as f:
                                # Se removió el 'mime' forzado para que descargue cualquier formato bien
                                columnas[i].download_button(label=f"⬇️ {archivo}", data=f, file_name=archivo, key=f"btn_{carpeta}_{archivo}_{index}")
                    else:
                        st.info("Carpeta sin fotos válidas.")

with tab2:
    st.subheader("Top Terminales con más Ganadores")
    if 'NOMBRE DE TERMINAL' in df.columns and col_fecha:
        fechas_validas = df[col_fecha].dropna()
        if not fechas_validas.empty:
            rango_fechas = st.date_input("Rango de fechas:", [fechas_validas.min().date(), fechas_validas.max().date()])
            if len(rango_fechas) == 2:
                mask = (df[col_fecha].dt.date >= rango_fechas[0]) & (df[col_fecha].dt.date <= rango_fechas[1])
                df_ranking = df.loc[mask]
            else:
                df_ranking = df
            
            ranking = df_ranking['NOMBRE DE TERMINAL'].value_counts().reset_index()
            ranking.columns = ['Terminal', 'Ganadores']
            
            if not ranking.empty:
                col_grafico, col_tabla = st.columns([2, 1])
                with col_grafico: st.bar_chart(data=ranking.head(10), x='Terminal', y='Ganadores')
                with col_tabla: st.dataframe(ranking, use_container_width=True)
            else:
                st.info("No hay datos en esta fecha.")

with tab3:
    st.subheader("🏪 Gestor de Terminales")
    df_term_editado = st.data_editor(df_terminales, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Cambios en Terminales"):
        df_term_editado.to_csv("terminales.csv", index=False)
        st.success("¡Base de datos actualizada!")
