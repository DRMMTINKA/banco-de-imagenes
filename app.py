import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
from github import Github
import base64
import io
import google.generativeai as genai

st.set_page_config(page_title="Ganadores de Premios Secundarios", layout="wide")

# =========================================================
# CONFIGURACIÓN DE GEMINI IA (SELECCIÓN DINÁMICA)
# =========================================================
modelo_ia = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Le pedimos a Google la lista exacta de modelos permitidos para tu llave
        modelos_disponibles = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Limpiamos el nombre por si viene con el prefijo 'models/'
                nombre = m.name.replace('models/', '')
                modelos_disponibles.append(nombre)
        
        if modelos_disponibles:
            # Buscamos el modelo más rápido ('flash') o nos quedamos con el primero que funcione
            modelo_elegido = next((m for m in modelos_disponibles if 'flash' in m), modelos_disponibles[0])
            modelo_ia = genai.GenerativeModel(modelo_elegido)
    except Exception as e:
        st.error(f"Error interno al cargar modelos de Google: {e}")

# =========================================================
# INYECCIÓN DE FUENTE CORPORATIVA DUPLET (.woff2)
# =========================================================
def aplicar_fuente_corporativa():
    try:
        with open("Duplet-Regular.woff2", "rb") as f:
            fuente_regular = base64.b64encode(f.read()).decode("utf-8")
        with open("Duplet-Bold.woff2", "rb") as f:
            fuente_bold = base64.b64encode(f.read()).decode("utf-8")
        
        css_fuente = f"""
        <style>
        @font-face {{
            font-family: 'Duplet';
            src: url(data:font/woff2;charset=utf-8;base64,{fuente_regular}) format('woff2');
            font-weight: normal;
            font-style: normal;
        }}
        @font-face {{
            font-family: 'Duplet';
            src: url(data:font/woff2;charset=utf-8;base64,{fuente_bold}) format('woff2');
            font-weight: bold;
            font-style: normal;
        }}
        html, body, .stApp, p, h1, h2, h3, h4, h5, h6, div, span, label, button {{
            font-family: 'Duplet', sans-serif !important;
        }}
        .material-symbols-rounded, 
        [data-testid="stIconMaterial"], 
        i.material-icons,
        span.material-symbols-rounded {{
            font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        }}
        </style>
        """
        st.markdown(css_fuente, unsafe_allow_html=True)
    except Exception as e:
        pass

aplicar_fuente_corporativa()

# =========================================================
# SISTEMA DE LOGIN Y SEGURIDAD
# =========================================================
def verificar_contrasena():
    if "acceso_concedido" not in st.session_state:
        st.session_state["acceso_concedido"] = False

    if not st.session_state["acceso_concedido"]:
        st.title("🔒 Acceso Restringido")
        st.write("Por favor, ingresa tus credenciales para acceder a la plataforma.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                usuario = st.text_input("Usuario")
                contrasena = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
                if submit:
                    try:
                        if usuario in st.secrets["usuarios"] and st.secrets["usuarios"][usuario] == contrasena:
                            st.session_state["acceso_concedido"] = True
                            st.session_state["usuario_actual"] = usuario
                            st.rerun()
                        else:
                            st.error("❌ Usuario o contraseña incorrectos.")
                    except Exception as e:
                        st.error("Error del sistema: No se han configurado los usuarios en Streamlit Secrets.")
        return False
    return True

if not verificar_contrasena():
    st.stop()

col_titulo, col_logout = st.columns([4, 1])
with col_titulo:
    st.title("🏆 Ganadores de Premios Secundarios")
with col_logout:
    st.write("")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["acceso_concedido"] = False
        st.rerun()

# =========================================================
# CÓDIGO PRINCIPAL
# =========================================================
def sincronizar_con_github(ruta_local, ruta_github, mensaje):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo("DRMMTINKA/banco-de-imagenes")
        with open(ruta_local, "rb") as f:
            content = f.read()
        try:
            contents = repo.get_contents(ruta_github)
            repo.update_file(contents.path, mensaje, content, contents.sha)
        except:
            repo.create_file(ruta_github, mensaje, content)
        return True
    except Exception as e:
        st.error(f"Hubo un problema de conexión con GitHub: {e}")
        return False

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

col_producto = next((c for c in df.columns if 'PRODUCTO' in c), 'PRODUCTO')
col_promotora = next((c for c in df.columns if 'PROMOTORA' in c), 'PROMOTORA')
col_req = next((c for c in df.columns if 'CUMPLE' in c or 'REQUISIT' in c), '¿CUMPLE REQUISITOS?')
col_fecha = next((c for c in df.columns if 'FECHA DE CARGA' in c), next((c for c in df.columns if 'FECHA' in c and 'PUB' not in c), 'FECHA DE CARGA'))
col_carpeta = next((c for c in df.columns if 'CARPET' in c), 'NOMBRE DE CARPETA')
col_ganador = next((c for c in df.columns if 'GANADOR' in c), 'NOMBRE GANADOR')
col_monto = next((c for c in df.columns if 'MONTO' in c), 'MONTO')
col_pub = next((c for c in df.columns if 'PUBLICACI' in c), None)

if not col_pub:
    df['FECHA PUBLICACIÓN'] = ""
    col_pub = 'FECHA PUBLICACIÓN'

if col_fecha in df.columns:
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

# --- BARRA LATERAL ---
st.sidebar.markdown(f"👤 **Usuario Activo:** `{st.session_state['usuario_actual']}`")
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
    nuevo_producto = st.selectbox("Producto", ["TINKA", "KÁBALA", "RAPITINKA", "GANA DIARIO"])
    nueva_promotora = st.text_input("Nombre de la Promotora")
    nuevo_monto = st.text_input("Monto (Ej: 100)")
    nuevo_requisitos = st.selectbox("¿Cumple Requisitos?", ["SÍ", "NO"])
    nueva_fecha = st.date_input("Fecha de Carga")
    nuevo_ganador = st.text_input("Nombre del Ganador")
    st.info("📁 El Código de Carpeta se generará automáticamente.")
    fotos = st.file_uploader("Fotos (Ganador y Acta)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp'])
    enviado = st.form_submit_button("Guardar Registro", type="primary")
    
    if enviado:
        if term_seleccionado == "":
            st.error("Falta seleccionar Terminal.")
        elif not fotos:
            st.error("Debes subir al menos una foto.")
        else:
            with st.spinner("Guardando en GitHub..."):
                fecha_str = nueva_fecha.strftime("%Y%m%d")
                if col_carpeta in df.columns:
                    carpetas_existentes = df[col_carpeta].dropna().astype(str)
                    carpetas_hoy = carpetas_existentes[carpetas_existentes.str.startswith(fecha_str)]
                else:
                    carpetas_hoy = []
                
                max_corr = 0
                for c in carpetas_hoy:
                    try:
                        corr = int(c.split('-')[-1])
                        if corr > max_corr: max_corr = corr
                    except: pass
                        
                nuevo_corr = max_corr + 1
                nueva_carpeta = f"{fecha_str}-{nuevo_corr:02d}"

                os.makedirs(nueva_carpeta, exist_ok=True)
                for foto in fotos:
                    ruta_local_foto = os.path.join(nueva_carpeta, foto.name)
                    with open(ruta_local_foto, "wb") as f:
                        f.write(foto.getbuffer())
                    sincronizar_con_github(ruta_local_foto, f"{nueva_carpeta}/{foto.name}", f"Subida foto {foto.name}")
                
                nueva_fila = {c: "" for c in df.columns} 
                nueva_fila['TERMINAL'] = term_seleccionado
                nueva_fila['NOMBRE DE TERMINAL'] = nombre_auto
                nueva_fila['SUPERVISOR'] = super_auto
                nueva_fila[col_producto] = nuevo_producto
                nueva_fila[col_promotora] = nueva_promotora
                nueva_fila[col_monto] = nuevo_monto
                nueva_fila[col_req] = nuevo_requisitos
                nueva_fila[col_fecha] = pd.to_datetime(nueva_fecha)
                nueva_fila[col_ganador] = nuevo_ganador
                nueva_fila[col_carpeta] = nueva_carpeta
                
                df_final = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
                df_final.to_excel("datos.xlsx", index=False)
                
                sincronizar_con_github("datos.xlsx", "datos.xlsx", f"Nuevo registro: {nuevo_ganador}")
                st.success(f"✅ ¡Guardado con éxito! Carpeta: {nueva_carpeta}")

# --- ÁREA CENTRAL ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Base de Datos", "📈 Estadísticas", "🏪 Maestro de Terminales", "🤖 Asistente IA"])

with tab1:
    if col_fecha in df.columns:
        df_mostrar = df.sort_values(by=col_fecha, ascending=False)
    else:
        df_mostrar = df.iloc[::-1]
        
    st.subheader("📥 Archivos Recientes")
    
    if "num_fotos" not in st.session_state:
        st.session_state["num_fotos"] = 5
        
    df_fotos = df_mostrar.head(st.session_state["num_fotos"])
    
    if col_carpeta in df.columns and col_ganador in df.columns:
        for index, row in df_fotos.iterrows():
            carpeta = str(row[col_carpeta]).strip()
            ganador = str(row[col_ganador]).strip()
            str_prod = f" | 🎟️ {str(row[col_producto]).strip()}" if col_producto in df.columns and pd.notna(row[col_producto]) and str(row[col_producto]).strip() != "" else ""
            str_monto = f" | 💰 S/ {str(row[col_monto]).strip()}" if col_monto in df.columns and pd.notna(row[col_monto]) and str(row[col_monto]).strip() != "" else ""
            
            val_pub = str(row[col_pub]).strip().lower()
            esta_publicado = False
            if val_pub in ["", "nan", "nat", "none"]:
                str_pub = " | 🔴 SIN PUBLICAR"
            else:
                str_pub = f" | 🟢 PUBLICADO ({val_pub})"
                esta_publicado = True
            
            etiqueta = ""
            if col_fecha in df.columns and pd.notna(row[col_fecha]):
                if (datetime.now() - row[col_fecha]).days <= 3:
                    etiqueta = " 🆕 NUEVO"
            
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
                        nueva_fecha_pub = st.date_input("Fecha de Publicación", key=f"date_pub_{carpeta}_{index}")
                    with col_btnpub:
                        st.write("") 
                        st.write("") 
                        if not esta_publicado:
                            if st.button("✅ Marcar Publicado", key=f"btn_upd_{carpeta}_{index}", use_container_width=True):
                                df.at[index, col_pub] = pd.to_datetime(nueva_fecha_pub).strftime('%Y-%m-%d')
                                df.to_excel("datos.xlsx", index=False)
                                sincronizar_con_github("datos.xlsx", "datos.xlsx", f"Publicado: {ganador}")
                                st.rerun()
                        else:
                            if st.button("❌ Revertir a 'Sin Publicar'", key=f"btn_rev_{carpeta}_{index}", use_container_width=True):
                                df.at[index, col_pub] = ""
                                df.to_excel("datos.xlsx", index=False)
                                sincronizar_con_github("datos.xlsx", "datos.xlsx", f"Revertido: {ganador}")
                                st.rerun()

    if len(df_mostrar) > st.session_state["num_fotos"]:
        if st.button("⬇️ VER MÁS FOTOS", use_container_width=True):
            st.session_state["num_fotos"] += 5
            st.rerun()

    st.markdown("---")
    
    col_tit_tabla, col_btn_tabla = st.columns([4, 1])
    with col_tit_tabla:
        st.subheader("📊 Tabla de Registros")
    with col_btn_tabla:
        st.write("")
        df_excel = df_mostrar.astype(str)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Registros')
        
        st.download_button(
            label="📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"Registros_Tinka_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.dataframe(df_mostrar.astype(str), use_container_width=True)

with tab2:
    st.subheader("📈 Panel de Estadísticas")
    
    color_naranja = "#FF5F00"
    color_verde = "#006820"
    color_verde_limon = "#B5E53E"
    color_rojo = "#E5001F"
    color_amarillo = "#FFED00"
    
    def aplicar_filtros_locales(df_origen, key_prefix):
        df_res = df_origen.copy()
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if col_fecha in df_res.columns:
                fechas_validas = df_res[col_fecha].dropna()
                if not fechas_validas.empty:
                    min_d = fechas_validas.min().date()
                    max_d = fechas_validas.max().date()
                    rango = st.date_input("Rango de fechas", [min_d, max_d], key=f"date_{key_prefix}")
                    if len(rango) == 2:
                        mask = (df_res[col_fecha].dt.date >= rango[0]) & (df_res[col_fecha].dt.date <= rango[1])
                        df_res = df_res.loc[mask]
        with col_f2:
            if col_producto in df_res.columns:
                prods = sorted([str(p) for p in df_res[col_producto].unique() if str(p).strip() != ""])
                sel_prods = st.multiselect("Producto", prods, default=prods, key=f"prod_{key_prefix}")
                if sel_prods:
                    df_res = df_res[df_res[col_producto].isin(sel_prods)]
        return df_res

    st.markdown("---")
    
    col_tit_ev, col_op_ev = st.columns([3, 1])
    with col_tit_ev:
        st.markdown("### 📅 Evolución de Ganadores")
    with col_op_ev:
        st.write("")
        agrupacion_ev = st.radio("Agrupar gráfico por:", ["Días", "Meses"], horizontal=True, key="radio_ev")
        
    df_ev = aplicar_filtros_locales(df, "ev")
    if not df_ev.empty and col_fecha in df.columns:
        if agrupacion_ev == "Días":
            evolutivo = df_ev.groupby(df_ev[col_fecha].dt.date).size().reset_index(name='Cantidad')
            evolutivo.columns = ['Fecha', 'Cantidad']
        else:
            df_ev['Mes_Str'] = df_ev[col_fecha].dt.strftime('%Y-%m')
            evolutivo = df_ev.groupby('Mes_Str').size().reset_index(name='Cantidad')
            evolutivo.columns = ['Fecha', 'Cantidad']
            
        fig_line = px.line(evolutivo, x='Fecha', y='Cantidad', markers=True)
        fig_line.update_traces(line_color=color_naranja, marker=dict(color=color_naranja))
        
        if agrupacion_ev == "Meses":
            fig_line.update_layout(xaxis_type='category')
            
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar con estos filtros.")

    st.markdown("---")
    st.markdown("### 🏅 Top Promotoras")
    df_prom = aplicar_filtros_locales(df, "prom")
    if not df_prom.empty and col_promotora in df.columns:
        ranking_p = df_prom[col_promotora].value_counts().reset_index()
        ranking_p.columns = ['Promotora', 'Apariciones']
        fig_p = px.bar(ranking_p.head(10), x='Promotora', y='Apariciones', text_auto=True)
        fig_p.update_traces(marker_color=color_verde)
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏆 Top Terminales")
    df_term = aplicar_filtros_locales(df, "term")
    if not df_term.empty and 'NOMBRE DE TERMINAL' in df.columns:
        ranking_t = df_term['NOMBRE DE TERMINAL'].value_counts().reset_index()
        ranking_t.columns = ['Terminal', 'Ganadores']
        fig_bar = px.bar(ranking_t.head(10), x='Terminal', y='Ganadores', text_auto=True)
        fig_bar.update_traces(marker_color=color_amarillo)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📢 Material Publicado")
    df_pub = df.copy()
    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
    
    df_pub['fecha_pub_dt'] = pd.to_datetime(df_pub[col_pub], errors='coerce')
    
    with col_f3:
        st.write("")
        tipo_filtro = st.radio("Filtrar fechas por:", ["Fecha de Carga", "Fecha de Publicación"], key="radio_pub")
        
    with col_f1:
        if tipo_filtro == "Fecha de Carga" and col_fecha in df_pub.columns:
            fechas_validas = df_pub[col_fecha].dropna()
        else:
            fechas_validas = df_pub['fecha_pub_dt'].dropna()
            
        if not fechas_validas.empty:
            min_d = fechas_validas.min().date()
            max_d = fechas_validas.max().date()
            rango = st.date_input("Rango de fechas", [min_d, max_d], key="date_pub")
            if len(rango) == 2:
                if tipo_filtro == "Fecha de Carga":
                    mask = (df_pub[col_fecha].dt.date >= rango[0]) & (df_pub[col_fecha].dt.date <= rango[1])
                    df_pub = df_pub.loc[mask]
                else:
                    mask_pub = (df_pub['fecha_pub_dt'].dt.date >= rango[0]) & (df_pub['fecha_pub_dt'].dt.date <= rango[1])
                    mask_unpub = df_pub['fecha_pub_dt'].isna()
                    df_pub = df_pub.loc[mask_pub | mask_unpub]
                    
    with col_f2:
        if col_producto in df_pub.columns:
            prods = sorted([str(p) for p in df_pub[col_producto].unique() if str(p).strip() != ""])
            sel_prods = st.multiselect("Producto", prods, default=prods, key="prod_pub")
            if sel_prods:
                df_pub = df_pub[df_pub[col_producto].isin(sel_prods)]

    if not df_pub.empty and col_pub:
        estados = ["Sin Publicar" if str(v).strip().lower() in ["", "nan", "nat", "none"] else "Publicado" for v in df_pub[col_pub]]
        df_estados = pd.DataFrame({'Estado': estados})
        conteo = df_estados['Estado'].value_counts().reset_index()
        conteo.columns = ['Estado', 'Cantidad']
        fig_pub = px.pie(conteo, values='Cantidad', names='Estado', hole=0.4, color='Estado', 
                         color_discrete_map={"Publicado": color_verde_limon, "Sin Publicar": color_rojo})
        st.plotly_chart(fig_pub, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar con estos filtros.")

with tab3:
    st.subheader("🏪 Gestor de Terminales")
    df_term_editado = st.data_editor(df_terminales, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar Cambios en Terminales"):
        df_term_editado.to_csv("terminales.csv", index=False)
        sincronizar_con_github("terminales.csv", "terminales.csv", "Catálogo actualizado")
        st.success("¡Base de datos actualizada!")

with tab4:
    st.subheader("🤖 Asistente Analista de La Tinka")
    st.markdown("Pregúntame cualquier dato sobre los ganadores, montos, terminales o estados de publicación.")
    
    if modelo_ia is None:
        st.error("⚠️ Hubo un problema al conectar con Gemini. Verifica que tu API Key sea correcta o intenta hacer 'Reboot'.")
    else:
        if "mensajes_chat" not in st.session_state:
            st.session_state.mensajes_chat = []
            
        for mensaje in st.session_state.mensajes_chat:
            with st.chat_message(mensaje["rol"]):
                st.markdown(mensaje["contenido"])
                
        pregunta_usuario = st.chat_input("Ejemplo: ¿Cuántas fotos de Tinka faltan publicar?")
        
        if pregunta_usuario:
            with st.chat_message("user"):
                st.markdown(pregunta_usuario)
            st.session_state.mensajes_chat.append({"rol": "user", "contenido": pregunta_usuario})
            
            datos_csv = df.to_csv(index=False)
            prompt_contexto = f"""
            Actúa como un experto analista de datos para la marca de lotería peruana 'La Tinka'.
            A continuación te entrego la base de datos actualizada con los registros de ganadores y fotos subidas:
            
            {datos_csv}
            
            Reglas importantes para tus respuestas:
            1. Responde basándote EXCLUSIVAMENTE en los datos de arriba.
            2. Sé breve, amable, profesional y directo al grano.
            3. Si te preguntan algo que no está en la tabla, di amablemente que no tienes esa información.
            
            Pregunta del usuario: {pregunta_usuario}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Analizando la base de datos..."):
                    try:
                        respuesta = modelo_ia.generate_content(prompt_contexto)
                        texto_respuesta = respuesta.text
                        st.markdown(texto_respuesta)
                        st.session_state.mensajes_chat.append({"rol": "assistant", "contenido": texto_respuesta})
                    except Exception as e:
                        st.error(f"Ocurrió un error al procesar la respuesta: {e}")
