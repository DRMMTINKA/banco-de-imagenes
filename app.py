import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

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
col_fecha = next((c for c in df.columns if 'FECHA DE CARGA' in c), next((c for c in df.columns if 'FECHA' in c and 'PUB' not in c), None))
col_carpeta = next((c for c in df.columns if 'CARPET' in c), None)
col_ganador = next((c for c in df.columns if 'GANADOR' in c), None)
col_monto = next((c for c in df.columns if 'MONTO' in c), None)

col_pub = next((c for c in df.columns if 'PUBLICACI' in c), None)
if not col_pub:
    df['FECHA PUBLICACIÓN'] = ""
    col_pub = 'FECHA PUBLICACIÓN'

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
    nuevo_monto = st.text_input("Monto (Ej: 100)")
    nueva_fecha = st.date_input("Fecha de Carga")
    nuevo_ganador = st.text_input("Nombre del Ganador")
    nueva_carpeta = st.text_input("Código de Carpeta (Ej: 20261006-01)")
    
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
            if col_monto: nueva_fila[col_monto] = nuevo_monto
            if col_fecha: nueva_fila[col_fecha] = pd.to_datetime(nueva_fecha)
            if col_ganador: nueva_fila[col_ganador] = nuevo_ganador
            if col_carpeta: nueva_fila[col_carpeta] = nueva_carpeta
            
            df_final = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            df_final.to_excel("datos.xlsx", index=False)
            st.success(f"✅ ¡{nuevo_ganador} guardado!")

# ---------------------------------------------------------
# ÁREA CENTRAL: PESTAÑAS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Base de Datos", "📈 Estadísticas", "🏪 Maestro de Terminales"])

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
            
            str_prod = f" | 🎟️ {str(row[col_producto]).strip()}" if col_producto and pd.notna(row[col_producto]) and str(row[col_producto]).strip() != "" else ""
            str_monto = f" | 💰 S/ {str(row[col_monto]).strip()}" if col_monto and pd.notna(row[col_monto]) and str(row[col_monto]).strip() != "" else ""
            
            str_pub = ""
            val_pub = str(row[col_pub]).strip().lower()
            esta_publicado = False
            if val_pub in ["", "nan", "nat", "none"]:
                str_pub = " | 🔴 SIN PUBLICAR"
            else:
                str_pub = f" | 🟢 PUBLICADO ({val_pub})"
                esta_publicado = True
            
            etiqueta = ""
            if col_fecha and pd.notna(row[col_fecha]):
                if (datetime.now() - row[col_fecha]).days <= 3:
                    etiqueta = " 🆕 ¡NUEVA FOTO!"
            
            if carpeta != "" and os.path.exists(carpeta) and os.path.isdir(carpeta):
                with st.expander(f"👤 {ganador}{str_prod}{str_monto}{str_pub} (Código: {carpeta}){etiqueta}"):
                    archivos = [a for a in os.listdir(carpeta) if a.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    
                    if len(archivos) > 0:
                        columnas = st.columns(len(archivos))
                        for i, archivo in enumerate(archivos):
                            with open(os.path.join(carpeta, archivo), "rb") as f:
                                columnas[i].download_button(label=f"⬇️ {archivo}", data=f, file_name=archivo, key=f"btn_{carpeta}_{archivo}_{index}")
                    else:
                        st.info("Carpeta sin fotos válidas.")
                    
                    st.markdown("---")
                    col_fechapub, col_btnpub = st.columns([2, 1])
                    with col_fechapub:
                        nueva_fecha_pub = st.date_input("Seleccionar Fecha de Publicación", key=f"date_pub_{carpeta}_{index}")
                    with col_btnpub:
                        st.write("") 
                        st.write("") 
                        if not esta_publicado:
                            if st.button("✅ Marcar como Publicado", key=f"btn_upd_{carpeta}_{index}", use_container_width=True):
                                df.at[index, col_pub] = pd.to_datetime(nueva_fecha_pub).strftime('%Y-%m-%d')
                                df.to_excel("datos.xlsx", index=False)
                                st.rerun()
                        else:
                            if st.button("❌ Revertir a 'Sin Publicar'", key=f"btn_rev_{carpeta}_{index}", use_container_width=True):
                                df.at[index, col_pub] = ""
                                df.to_excel("datos.xlsx", index=False)
                                st.rerun()

with tab2:
    st.subheader("📈 Panel de Estadísticas")
    st.info("💡 Los gráficos responden automáticamente al filtro de 'PRODUCTO' y al rango de fechas.")
    
    if col_fecha:
        fechas_validas = df[col_fecha].dropna()
        if not fechas_validas.empty:
            rango_fechas = st.date_input("Rango de fechas para estadísticas:", [fechas_validas.min().date(), fechas_validas.max().date()])
            if len(rango_fechas) == 2:
                mask = (df_filtrado[col_fecha].dt.date >= rango_fechas[0]) & (df_filtrado[col_fecha].dt.date <= rango_fechas[1])
                df_stats = df_filtrado.loc[mask]
            else:
                df_stats = df_filtrado
        else:
            df_stats = df_filtrado
            
        if not df_stats.empty:
            # 1. Gráfico Evolutivo de Fechas (Línea)
            st.markdown("### 📅 Evolución de Ganadores en el Tiempo")
            evolutivo = df_stats.groupby(df_stats[col_fecha].dt.date).size().reset_index(name='Cantidad de Fotos')
            evolutivo.columns = ['Fecha', 'Cantidad']
            
            fig_line = px.line(evolutivo, x='Fecha', y='Cantidad', markers=True, 
                               labels={'Fecha': 'Día', 'Cantidad': 'Nº de Ganadores Registrados'})
            fig_line.update_layout(yaxis_title="Cantidad", margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_line, use_container_width=True)
            
            st.markdown("---")
            
            col_g1, col_g2 = st.columns(2)
            
            # 2. Material Publicado vs Sin Publicar
            with col_g1:
                st.markdown("### 📢 Material Publicado")
                estados = ["Sin Publicar" if str(v).strip().lower() in ["", "nan", "nat", "none"] else "Publicado" for v in df_stats[col_pub]]
                df_estados = pd.DataFrame({'Estado': estados})
                conteo_estados = df_estados['Estado'].value_counts().reset_index()
                conteo_estados.columns = ['Estado', 'Cantidad']
                
                fig_pub = px.pie(conteo_estados, values='Cantidad', names='Estado', hole=0.4, 
                                 color='Estado', color_discrete_map={"Publicado": "#2ecc71", "Sin Publicar": "#e74c3c"})
                fig_pub.update_traces(textposition='inside', textinfo='percent+label')
                fig_pub.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pub, use_container_width=True)
                
            # 3. Ranking de Terminales
            with col_g2:
                st.markdown("### 🏆 Top Terminales (Ranking)")
                if 'NOMBRE DE TERMINAL' in df.columns:
                    ranking = df_stats['NOMBRE DE TERMINAL'].value_counts().reset_index()
                    ranking.columns = ['Terminal', 'Ganadores']
                    
                    fig_bar = px.bar(ranking.head(10), x='Terminal', y='Ganadores', text_auto=True)
                    fig_bar.update_layout(xaxis_title="", yaxis_title="Ganadores", margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No hay ganadores registrados en este rango de fechas con este producto.")
    else:
        st.error("No se detectó una columna de FECHA válida para generar estadísticas.")

with tab3:
    st.subheader("🏪 Gestor de Terminales")
    df_term_editado = st.data_editor(df_terminales, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Cambios en Terminales"):
        df_term_editado.to_csv("terminales.csv", index=False)
        st.success("¡Base de datos actualizada!")
