import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .haus-card { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stButton>button { 
        width: 100%; 
        background-color: #0C2D33 !important; 
        color: white !important; 
        font-weight: bold; 
        border-radius: 10px; 
        height: 3em; 
    }
    </style>
    """, unsafe_allow_html=True)

DISTRITOS = ["Arganzuela", "Centro", "Chamberí", "Retiro", "Salamanca", "Tetuán", "Otros"]

# --- FUNCIÓN DE ENVÍO ---
def save_to_supabase(data: Dict[str, Any]):
    try:
        # Credenciales de tus Secrets
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
        from supabase import create_client
        supabase = create_client(url, key)
        
        # Insertar datos en la tabla
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# --- INTERFAZ ---
st.title("🏠 HausMate Match")

with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("form_final"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo *")
            whatsapp = st.text_input("WhatsApp *")
        with col2:
            presupuesto = st.number_input("Presupuesto (€)", 0, 5000, 800)
            preferencia = st.selectbox("Preferencia", ["Mixto", "Hombres", "Mujeres"])
        
        # Selección de zonas
        zonas_seleccionadas = st.multiselect("📍 Zonas de interés", options=DISTRITOS)
        
        # Mapa de Madrid
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=200, use_container_width=True, key="mapa_madrid")
        
        notas = st.text_area("Notas adicionales")
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre or not whatsapp:
        st.error("⚠️ El nombre y el WhatsApp son obligatorios.")
    else:
        # PAYLOAD CORREGIDO: "zona" coincide con tu columna de Supabase
        payload = {
            "full_name": nombre,
            "whatsapp": whatsapp,
            "budget": presupuesto,
            "living_with": preferencia,
            "zona": zonas_seleccionadas,  # <--- Cambio clave aquí
            "notes": notas,
            "created_at": dt.datetime.now().isoformat()
        }
        
        with st.spinner("Guardando en la base de datos..."):
            exito, error_msg = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("✅ ¡Enviado con éxito! Ya puedes ver tu registro en Supabase.")
            else:
                st.error("❌ Error al guardar.")
                st.info(f"Detalle técnico: {error_msg}")
