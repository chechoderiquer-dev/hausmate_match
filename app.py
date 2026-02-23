import os
import datetime as dt
from typing import Dict, Any
import streamlit as st
import folium
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(page_title="HausMate Match", page_icon="🏠", layout="centered")

# Estilo visual
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #7FBBC2 0%, #D9F1F3 60%, #ffffff 100%); }
    .haus-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stButton>button { width: 100%; background-color: #0C2D33; color: white; font-weight: bold; height: 3rem; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Lista de distritos fija para evitar errores 404
DISTRITOS = [
    "Arganzuela", "Barajas", "Carabanchel", "Centro", "Chamartín", "Chamberí", 
    "Ciudad Lineal", "Fuencarral-El Pardo", "Hortaleza", "Latina", "Moncloa-Aravaca", 
    "Moratalaz", "Puente de Vallecas", "Retiro", "Salamanca", "San Blas-Canillejas", 
    "Tetuán", "Usera", "Vicálvaro", "Villa de Vallecas", "Villaverde"
]

def save_to_supabase(data: Dict[str, Any]):
    try:
        # Limpiamos espacios por si acaso
        url = st.secrets["SUPABASE_URL"].strip().replace('"', '')
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"].strip().replace('"', '')
        table = st.secrets["SUPABASE_TABLE"].strip().replace('"', '')
        
        from supabase import create_client
        supabase = create_client(url, key)
        supabase.table(table).insert(data).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

# Interfaz
st.title("🏠 HausMate Match")
st.markdown("Encuentra tu match ideal en Madrid")

with st.container():
    st.markdown('<div class="haus-card">', unsafe_allow_html=True)
    with st.form("form_registro"):
        st.subheader("📝 Tu perfil de búsqueda")
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre completo *")
            whatsapp = st.text_input("WhatsApp *")
        with c2:
            presupuesto = st.number_input("Presupuesto Max (€)", 0, 5000, 800)
            preferencia = st.selectbox("Preferencia", ["Mixto", "Hombres", "Mujeres"])
        
        distritos_sel = st.multiselect("📍 ¿Dónde quieres vivir?", options=DISTRITOS)
        
        # Mapa simple
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
        st_folium(m, height=250, use_container_width=True)
        
        notas = st.text_area("Notas adicionales")
        enviar = st.form_submit_button("ENVIAR MI PERFIL")
    st.markdown('</div>', unsafe_allow_html=True)

if enviar:
    if not nombre or not whatsapp:
        st.error("⚠️ Por favor, rellena el nombre y el WhatsApp.")
    else:
        payload = {
            "full_name": nombre,
            "whatsapp": whatsapp,
            "budget": presupuesto,
            "living_with": preferencia,
            "barrios": distritos_sel,
            "notes": notas,
            "created_at": dt.datetime.now().isoformat()
        }
        
        with st.spinner("Conectando con la base de datos..."):
            exito, error = save_to_supabase(payload)
            if exito:
                st.balloons()
                st.success("¡Perfecto! Datos guardados correctamente.")
            else:
                st.error("❌ Error al enviar.")
                st.info(f"Detalle técnico: {error}")
