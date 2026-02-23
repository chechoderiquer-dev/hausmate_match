import os
import datetime as dt
import hashlib
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO PERSONALIZADO ---
def apply_custom_style():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
        .haus-card { 
            background: white; 
            padding: 2.5rem; 
            border-radius: 20px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        }
        .logo-container { text-align: center; padding-bottom: 20px; }
        .stButton>button { 
            width: 100%; 
            background-color: #0C2D33 !important; 
            color: white !important; 
            font-weight: bold; 
            border-radius: 12px; 
            height: 3.5em; 
            border: none;
        }
        /* Ajuste de inputs para que se vean más limpios */
        .stTextInput>div>div>input, .stSelectbox>div>div>div { border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)

apply_custom_style()

# --- MOSTRAR LOGO ---
# Usando el nombre que analicé de tu archivo: LOGO_HAUSMATE.png
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
try:
    st.image("LOGO_HAUSMATE.png", width=350) # Tamaño ajustado para que luzca
except:
    st.markdown("<h1 style='text-align: center; color: #0C2D33;'>HAUSMATE</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- CONFIGURACIÓN DE OPCIONES ---
DISTRITOS = ["Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Moncloa", "Arganzuela", "Malasaña", "Lavapiés", "Otros"]
IDIOMAS = ["Spanish", "English", "French", "German", "Italian", "Portuguese", "Other"]

def save_to_supabase(data: Dict[str, Any]):
    try:
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        from supabase import create_client
        supabase = create_client(url, key)
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- FORMULARIO ---
with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("form_match"):
        st.subheader("📝 Encuentra tu HausMate")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo *")
            tel = st.text_input("WhatsApp (con prefijo +34) *")
            edad = st.number_input("Edad", 18, 99, 25)
            genero = st.selectbox("Tu género", ["mujer", "hombre", "otro"])
            idioma = st.selectbox("Idioma principal", options=IDIOMAS)
        
        with col2:
            budget = st.number_input("Presupuesto Máximo (€)", 0, 5000, 1000)
            pref_gen = st.selectbox("Preferencia de convivencia", ["mixto", "solo_mujeres", "solo_hombres"])
            # Sincronizado con columna 'max_compartir_con'
            max_comp = st.selectbox("Máximo de personas en casa", [1, 2, 3, 4, 5])
            # Sincronizado con columna 'banos_min'
            banos = st.selectbox("Mínimo de baños", [1, 2, 3])
        
        st.write("📍 **Zonas preferidas**")
        zona_sel = st.multiselect("Puedes elegir varias", options=DISTRITOS)
        
        c3, c4 = st.columns(2)
        with c3:
            f_inicio = st.date_input("¿Cuándo quieres entrar?", dt.date.today())
        with c4:
            f_fin = st.date_input("¿Hasta cuándo te quedas?", dt.date.today() + dt.timedelta(days=180))
            
        notas = st.text_area("Cuéntanos un poco sobre ti (hobbies, trabajo...)")
        
        # Mapa estético de Madrid
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_v10")
        
        enviar = st.form_submit_button("¡REGISTRARME Y BUSCAR MATCH!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE ENVÍO ---
if enviar:
    if not nombre or not tel:
        st.error("⚠️ El nombre y el teléfono son obligatorios para contactarte.")
    else:
        # Generar clave única para evitar duplicados (Dedupe Key)
        unique_id = hashlib.md5(f"{tel}_{dt.datetime.now()}".encode()).hexdigest()
        
        # Mapeo exacto a tu tabla de Supabase y archivo CSV
        payload = {
            "nombre": nombre,
            "telefono": tel,
            "telefono_raw": tel,
            "edad": int(edad),
            "genero": genero,
            "pref_genero": pref_gen,
            "idioma": idioma,
            "zona": "|".join(zona_sel),
            "budget": int(budget),
            "inicio": f_inicio.isoformat(),
            "fin": f_fin.isoformat(),
            "max_compartir_con": int(max_comp), # Columna correcta según tu CSV
            "banos_min": int(banos),            # Columna correcta según tu CSV
            "notas": notas,
            "dedupe_key": unique_id,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Conectando con HausMate..."):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡Perfecto! Tus datos han sido guardados. Estamos buscándote el mejor match.")
            else:
                st.error(f"Hubo un problema al guardar: {error}")
