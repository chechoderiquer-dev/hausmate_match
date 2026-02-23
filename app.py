import os
import json
import datetime as dt
from typing import List, Dict, Any

import streamlit as st
import pandas as pd

import folium
from streamlit_folium import st_folium

# =========================
# BRAND / UI
# =========================
APP_NAME = "HausMate Match"
LOGO_PATH_LOCAL = "logo.png"

BRAND_BG = "#7FBBC2"
BRAND_BG_2 = "#D9F1F3"
BRAND_DARK = "#0C2D33"
WHITE = "#FFFFFF"

def brand_css():
    st.markdown(
        f"""
        <style>
          .stApp {{
            background: linear-gradient(180deg, {BRAND_BG} 0%, {BRAND_BG_2} 60%, #ffffff 100%);
          }}
          .block-container {{ padding-top: 2rem; }}
          h1, h2, h3, h4, h5, h6, p, label, div {{ color: {BRAND_DARK} !important; }}
          .haus-card {{
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(12,45,51,0.12);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 6px 18px rgba(12,45,51,0.10);
          }}
          .stButton > button {{
            background: {BRAND_DARK};
            color: {WHITE} !important;
            border-radius: 12px;
            border: 0;
            width: 100%;
            font-weight: bold;
            height: 3em;
          }}
          .stTextInput>div>div>input, .stSelectbox>div>div>div {{
            background-color: #f8f9fa !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_header():
    col1, col2 = st.columns([1, 4], vertical_alignment="center")
    with col1:
        if os.path.exists(LOGO_PATH_LOCAL):
            st.image(LOGO_PATH_LOCAL, use_container_width=True)
        else:
            st.markdown(f"<h1>🏠</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h1 style='margin:0;'>{APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0; opacity:0.8;'>Encuentra tu match ideal en Madrid</p>", unsafe_allow_html=True)

# =========================
# DATA: DISTRITOS DE MADRID (LOCAL - SIN DEPENDENCIAS)
# =========================
DISTRITOS_MADRID = [
    "Arganzuela", "Barajas", "Carabanchel", "Centro", "Chamartín", 
    "Chamberí", "Ciudad Lineal", "Fuencarral-El Pardo", "Hortaleza", 
    "Latina", "Moncloa-Aravaca", "Moratalaz", "Puente De Vallecas", 
    "Retiro", "Salamanca", "San Blas-Canillejas", "Tetuán", 
    "Usera", "Vicálvaro", "Villa De Vallecas", "Villaverde"
]

# =========================
# SECRETS & SUPABASE (CON LIMPIEZA DE URL)
# =========================
def get_secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except:
        pass
    return os.getenv(name, default).strip()

def get_supabase_client():
    # Limpiamos posibles espacios o comillas accidentales en los secrets
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        return None, "Faltan las credenciales SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en los Secrets de Streamlit."
    
    if not url.startswith("http"):
        return None, f"La URL de Supabase debe empezar con https://. Valor actual: {url}"

    try:
        from supabase import create_client
        return create_client(url, key), ""
    except Exception as e:
        return None, f"Error de configuración del cliente: {str(e)}"

def save_to_supabase(payload: Dict[str, Any]) -> (bool, str):
    table = get_secret("SUPABASE_TABLE", "hausmate_leads")
    client, err = get_supabase_client()
    if client is None:
        return False, err
    try:
        # Intentamos la inserción
        client.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, f"Error de conexión con la base de datos: {str(e)}"

# =========================
# APP PRINCIPAL
# =========================
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="centered")
brand_css()
render_header()

st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
st.subheader("📝 Tu perfil de búsqueda")

with st.form("survey_form"):
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Nombre completo *", placeholder="Ej. Juan Pérez")
        whatsapp = st.text_input("WhatsApp (con lada) *", placeholder="+34600000000")
    with col2:
        age = st.number_input("Edad", 18, 99, 25)
        budget = st.number_input("Presupuesto Max (€/mes)", 0, 5000, 800)

    col3, col4 = st.columns(2)
    with col3:
        rooms = st.selectbox("Habitaciones", ["1", "2", "3", "4+"])
    with col4:
        living_with = st.selectbox("Preferencia", ["Hombres", "Mujeres", "Mixto"])

    st.markdown("---")
    st.markdown("### 📍 ¿Dónde quieres vivir?")
    
    selected_distritos = st.multiselect(
        "Busca y selecciona distritos de Madrid", 
        options=DISTRITOS_MADRID
    )
    
    # Mapa simplificado de referencia (siempre carga)
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
    folium.Marker([40.4168, -3.7038], popup="Madrid Centro").add_to(m)
    st_folium(m, height=250, use_container_width=True, key="mapa_madrid")

    st.markdown("---")
    col5, col6 = st.columns(2)
    with col5:
        move_in = st.date_input("Fecha entrada", dt.date.today())
    with col6:
        move_out = st.date_input("Fecha salida", dt.date.today() + dt.timedelta(days=90))

    notes = st.text_area("Notas adicionales (rutina, mascotas, etc.)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("ENVIAR MI PERFIL")

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not full_name or not whatsapp:
        st.error("⚠️ Por favor, rellena el nombre y el WhatsApp.")
    else:
        # Preparamos los datos
        payload = {
            "full_name": full_name.strip(),
            "whatsapp": whatsapp.strip(),
            "age": int(age),
            "budget": int(budget),
            "rooms": rooms,
            "living_with": living_with,
            "barrios": selected_distritos,
            "move_in": str(move_in),
            "move_out": str(move_out),
            "notes": notes.strip(),
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }

        with st.spinner("Enviando tus datos..."):
            success, error_msg = save_to_supabase(payload)
            
            if success:
                st.balloons()
                st.success("✅ ¡Perfecto! Hemos recibido tu perfil. Te contactaremos pronto.")
            else:
                st.error(f"❌ Error al enviar.")
                with st.expander("Detalles técnicos del error"):
                    st.write(error_msg)
                    st.info("💡 Consejo: Revisa que la URL de Supabase en tus Secrets sea correcta y no tenga espacios.")
