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
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# DATA LOCAL: DISTRITOS DE MADRID
# =========================
DISTRITOS_MADRID = [
    "Arganzuela", "Barajas", "Carabanchel", "Centro", "Chamartín", 
    "Chamberí", "Ciudad Lineal", "Fuencarral-El Pardo", "Hortaleza", 
    "Latina", "Moncloa-Aravaca", "Moratalaz", "Puente De Vallecas", 
    "Retiro", "Salamanca", "San Blas-Canillejas", "Tetuán", 
    "Usera", "Vicálvaro", "Villa De Vallecas", "Villaverde"
]

# =========================
# SECRETS & SUPABASE (LIMPIEZA EXTREMA)
# =========================
def get_clean_secret(name: str) -> str:
    val = ""
    try:
        if name in st.secrets:
            val = str(st.secrets[name])
    except:
        val = os.getenv(name, "")
    # Limpia espacios, comillas dobles y simples accidentales
    return val.strip().replace('"', '').replace("'", "")

def get_supabase_client():
    url = get_clean_secret("SUPABASE_URL")
    key = get_clean_secret("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        return None, "Faltan credenciales en Secrets."
    
    try:
        from supabase import create_client
        # Forzamos que la URL sea un string limpio
        return create_client(url, key), ""
    except Exception as e:
        return None, f"Error de cliente: {str(e)}"

def save_to_supabase(payload: Dict[str, Any]) -> (bool, str):
    table = get_clean_secret("SUPABASE_TABLE") or "hausmate_leads"
    client, err = get_supabase_client()
    if client is None: return False, err
    try:
        client.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# =========================
# APP
# =========================
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="centered")
brand_css()

# Header
st.markdown(f"<h1 style='text-align: center;'>🏠 {APP_NAME}</h1>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    st.subheader("📝 Tu perfil de búsqueda")
    
    with st.form("survey_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Nombre completo *")
            whatsapp = st.text_input("WhatsApp *")
        with col2:
            age = st.number_input("Edad", 18, 99, 25)
            budget = st.number_input("Presupuesto Max (€)", 0, 5000, 800)

        col3, col4 = st.columns(2)
        with col3:
            rooms = st.selectbox("Habitaciones", ["1", "2", "3", "4+"])
        with col4:
            living_with = st.selectbox("Preferencia", ["Hombres", "Mujeres", "Mixto"])

        st.markdown("---")
        st.markdown("### 📍 ¿Dónde quieres vivir?")
        selected = st.multiselect("Selecciona distritos", options=DISTRITOS_MADRID)
        
        # Mapa estático de referencia para evitar errores de carga
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=250, use_container_width=True, key="mapa_fijo")

        st.markdown("---")
        notes = st.text_area("Notas adicionales")
        
        submitted = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not full_name or not whatsapp:
        st.error("Rellena nombre y WhatsApp.")
    else:
        payload = {
            "full_name": full_name,
            "whatsapp": whatsapp,
            "age": age,
            "budget": budget,
            "rooms": rooms,
            "living_with": living_with,
            "barrios": selected,
            "notes": notes,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Conectando con Supabase..."):
            success, error_msg = save_to_supabase(payload)
            if success:
                st.balloons()
                st.success("¡Enviado con éxito!")
            else:
                st.error("Error al enviar a la base de datos.")
                st.info(f"Detalle: {error_msg}")
