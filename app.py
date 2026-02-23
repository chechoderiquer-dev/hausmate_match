import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# =========================
# CONFIGURACIÓN Y ESTILO
# =========================
st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

def apply_style():
    st.markdown(
        """
        <style>
          .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
          .haus-card {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
          }
          .stButton > button { background: #0C2D33; color: white; width: 100%; border-radius: 10px; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# LÓGICA DE BASE DE DATOS
# =========================
def get_supabase_client():
    try:
        # Limpieza de posibles espacios o comillas accidentales
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '').replace("'", "")
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '').replace("'", "")
        
        from supabase import create_client
        return create_client(url, key), ""
    except Exception as e:
        return None, f"Error en configuración de Secrets: {str(e)}"

def save_lead(payload: Dict[str, Any]):
    client, err = get_supabase_client()
    if client is None:
        return False, err
    try:
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        client.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, f"Error de red o base de datos: {str(e)}"

# =========================
# INTERFAZ DE USUARIO
# =========================
apply_style()
st.markdown("<h1 style='text-align: center; color: #0C2D33;'>🏠 HausMate Match</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #0C2D33;'>Encuentra tu match ideal en Madrid</p>", unsafe_allow_html=True)

distritos = [
    "Arganzuela", "Barajas", "Carabanchel", "Centro", "Chamartín", 
    "Chamberí", "Ciudad Lineal", "Fuencarral-El Pardo", "Hortaleza", 
    "Latina", "Moncloa-Aravaca", "Moratalaz", "Puente de Vallecas", 
    "Retiro", "Salamanca", "San Blas-Canillejas", "Tetuán", 
    "Usera", "Vicálvaro", "Villa de Vallecas", "Villaverde"
]

with st.container():
    st.markdown("<div class='haus-card'>", unsafe_allow_html=True)
    with st.form("main_form"):
        st.subheader("📝 Tu perfil de búsqueda")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre completo *")
            phone = st.text_input("WhatsApp *", placeholder="+34...")
        with col2:
            budget = st.number_input("Presupuesto Max (€)", 0, 5000, 800)
            pref = st.selectbox("Preferencia de convivencia", ["Mixto", "Hombres", "Mujeres"])
        
        st.write("📍 **¿Dónde quieres vivir?**")
        barrios = st.multiselect("Selecciona distritos", options=distritos)
        
        # Mapa de referencia básico
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_fijo")
        
        notes = st.text_area("Notas adicionales")
        submitted = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not name or not phone:
        st.error("⚠️ Por favor, rellena el nombre y el WhatsApp.")
    else:
        # Formateo de datos
        data = {
            "full_name": name.strip(),
            "whatsapp": phone.strip(),
            "budget": int(budget),
            "living_with": pref,
            "barrios": barrios,
            "notes": notes.strip(),
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }
        
        with st.spinner("Conectando con la base de datos..."):
            success, error_msg = save_lead(data)
            if success:
                st.balloons()
                st.success("✅ ¡Recibido! Nos pondremos en contacto contigo pronto.")
            else:
                st.error("❌ Error al enviar.")
                with st.expander("Ver detalles técnicos del error"):
                    st.write(error_msg)
